#!/usr/bin/env python3

"""
Assertion-based tests for SHADER FILLS — `fillColor=<PaintShader>` on any
shape, and Text's shader mode built on top of it.

Pinned contract — a shader fill behaves EXACTLY like a color:
- it rides `fillColor` as per-frame STATE: the create snapshot / Args entries
  hold the PaintShader (serialized like gradients via jsonSerialization into
  a {"shader": ...} object the C++ discriminates on); persistence-until-
  changed and hide/fade-survival come from the metas step-function, and the
  C++ injects the shader into the effect chain per active frame — so there
  are NO shader effect entries in the Python stack at all;
- reassigning fillColor emits an ordinary Args entry at that frame (color or
  another paint — the C++ restarts the paint clock there);
- FILTERS (blur/grayscale/...) are rejected as fills with a TypeError;
- Text(fillColor=<paint>) builds the merged-silhouette structure (2 inputs,
  matte wired) and forwards later fill changes to its canvas.

The rendered behavior (persistence across fadeOut/fadeIn, switch landing on
its exact frame) is covered by feat.py's eyeballed checkpoints — it can't be
asserted from the Python stack alone.

Run directly: `python3 test/fill_shader_test.py`
"""

import json
import os
import sys
import tempfile

sys.path.insert(0, ".")
sys.path.insert(0, "test")
from helpers import check, section, summary

from videocode import serialize
from videocode.context import Context
from videocode.shader.ishader import PaintShader


def sceneFile(source: str) -> str:
    path = tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w")
    path.write(source)
    path.close()
    return path.name


def runScene(source: str) -> None:
    path = sceneFile(source)
    try:
        serialize.execScene(path)
    finally:
        os.remove(path)


def entriesWith(index: int, key: str) -> dict[int, dict]:
    return {f: e[key] for f, e in Context.stack[index].items() if f != -1 and key in e}


COMMON = "from videocode import *\n"

# ── the fill IS state: create snapshot holds the paint, no effect entries ───
section("Rectangle(fillColor=fire()) — per-frame state, not a timeline effect")

runScene(COMMON + "Rectangle(width=2, height=2, fillColor=fire())\nwait(3)\n")
idx = next(iter(Context.stack))
create = Context.stack[idx][-1]
check("create snapshot holds the PaintShader itself (like a color would be held)",
      isinstance(create["args"]["fillColor"], PaintShader))
check("NO shader effect entries — persistence is the C++'s per-frame injection",
      not entriesWith(idx, "MathShader"))

# ── serialization: the paint crosses to C++ as a {"shader": ...} object ─────
section("jsonSerialization — the shader object the C++ discriminates on")

path = sceneFile(COMMON + "Rectangle(width=2, height=2, fillColor=fire(speed=2))\nwait(1)\n")
try:
    payload = json.loads(serialize.serializeScene(path))
finally:
    os.remove(path)
fillJson = payload["stack"]["0"]["-1"]["args"]["fillColor"]
check("serializes with the discriminating 'shader' key", fillJson["shader"] == "MathShader")
check("carries filepath + numeric args", fillJson["filepath"].endswith("fire.glsl") and fillJson["speed"] == 2)

# ── reassignment = an ordinary Args entry at that frame ─────────────────────
section("fillColor reassignment — plain Args entries, like any color change")

runScene(COMMON + (
    "r = Rectangle(width=2, height=2, fillColor=fire())\n"
    "r.waitTo(60)\n"
    "r.fillColor = RED\n"
    "r.waitTo(90)\n"
    "r.fillColor = silk()\n"
    "wait(4)\n"
))
idx = next(iter(Context.stack))
argEntries = {f: e for f, e in Context.stack[idx].items()
              if f != -1 and any(k.startswith("Args") and "fillColor" in k for k in e)}
check("color switch lands as Args at frame 60", 60 in argEntries)
check("paint switch lands as Args at frame 90 (holding the new PaintShader)",
      90 in argEntries
      and isinstance(next(v for k, v in argEntries[90].items() if "fillColor" in k)["args"]["value"], PaintShader))
check("still no shader effect entries anywhere", not entriesWith(idx, "MathShader"))

# ── three shader kinds: paints are NOT fragments ─────────────────────────────
section("PaintShader is its own kind — filters can't type as fills")

from videocode.shader.ishader import FragmentShader
from videocode.shader.fragmentShader.fire import fire

check("a paint is not a FragmentShader (no hierarchy overlap)",
      not isinstance(fire(), FragmentShader))

# ── Text shader mode on top ──────────────────────────────────────────────────
section("Text(fillColor=starNest()) — merged-silhouette structure")

runScene(COMMON + 'Text("ABC", fontSize=1.5, fillColor=starNest())\nwait(2)\n')
check("exactly 2 inputs (canvas + word), letters never register", len(Context.stack) == 2)
canvasIdx = next(i for i in Context.stack if entriesWith(i, "Matte"))
wordIdx = next(i for i in Context.stack if i != canvasIdx)
check("canvas mattes the word",
      next(iter(entriesWith(canvasIdx, "Matte").values()))["args"]["source"] == wordIdx)
check("the canvas' fill IS the paint",
      isinstance(Context.stack[canvasIdx][-1]["args"]["fillColor"], PaintShader))

section("Text fill switch forwards to the canvas")

runScene(COMMON + (
    't = Text("HI", fillColor=fire())\n'
    "t.waitTo(60)\n"
    "t.fillColor = WHITE\n"
    "wait(4)\n"
))
canvasIdx = next(i for i in Context.stack if entriesWith(i, "Matte"))
check("the color change lands as an Args entry on the canvas at frame 60",
      any(k.startswith("Args") and "fillColor" in k for k in Context.stack[canvasIdx].get(60, {})))

section("letters-mode Text rejects switching to a shader fill")

try:
    runScene(COMMON + 't = Text("HI")\nt.fillColor = fire()\n')
    check("TypeError raised", False)
except TypeError:
    check("TypeError raised", True)

# ── apply() on a shader-mode Text: post-processes the fill ──────────────────
section("text.apply(fragment) — canvas only (fill-first order is C++-guaranteed)")

runScene(COMMON + (
    't = Text("HI", fillColor=fire())\n'
    "t.apply(blur(9), duration=2)\n"
    "wait(3)\n"
))
canvasIdx = next(i for i in Context.stack if entriesWith(i, "Matte"))
wordIdx = next(i for i in Context.stack if i != canvasIdx)
check("blur lands on the canvas", len(entriesWith(canvasIdx, "Blur")) == 1)
check("the word (mask) never receives fragment shaders", not entriesWith(wordIdx, "Blur"))

runScene(COMMON + 't = Text("GO", fillColor=fire())\nt.position(2, -1)\nwait(2)\n')
a, b = sorted(Context.stack.keys())
check("vertex shaders still reach both members",
      len(entriesWith(a, "Position")) == 1 and len(entriesWith(b, "Position")) == 1)

# ── wait(stop=...) — selective clock pausing; freeze = all ──────────────────
section("wait() gaps: stop selects paused clocks, freeze() = all of them")

runScene(COMMON + (
    'Text("HI", fillColor=fire())\n'
    "wait(1)\n"
    "wait(1, stop=Clock.PAINTS)\n"
    "wait(1, stop=[Clock.VIDEOS, Clock.EFFECTS])\n"
    "freeze(1)\n"
))
waits = [(e.start, e.n, e.stop) for e in Context.events if e.action == "Wait"]
check("four Wait events, back to back",
      len(waits) == 4 and all(waits[i][0] + waits[i][1] == waits[i + 1][0] for i in range(3)))
check("plain wait stops nothing", waits[0][2] == [])
check("stop=Clock.PAINTS pauses just the paints", waits[1][2] == ["paints"])
check("a list of clocks passes through (sorted)", waits[2][2] == ["effects", "videos"])
check("freeze() = a wait stopping ALL clocks", waits[3][2] == ["effects", "paints", "videos"])

# ── summary ──────────────────────────────────────────────────────────────────
summary()
