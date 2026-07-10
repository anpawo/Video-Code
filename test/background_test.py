#!/usr/bin/env python3

"""
Assertion-based tests for the `BG` script global — the scene's clear color.

Contract (resolved by serialize._applyBackground AFTER the scene runs):
- `BG = <plain rgba>` → `Context.backgroundColor = (r, g, b)` normalized 0..1,
  read by C++ in Core::executeStack exactly like lastEverAffectedFrame.
- No `BG` → None (renderer keeps its historical dark-gray default).
- `BG = <gradient>` → a gradient can't be a clear value, so a full-frame
  background `Rectangle` is created instead: visible from frame 0
  (noHiding) and layered behind everything (`background(offset=0)`, like
  `Plane`'s backdrop). `Context.backgroundColor` stays None.
- BG is COLOR-ONLY: non-color values are rejected with a TypeError
  (animated backgrounds stay explicit, e.g. `Plane().drift()`).
- Hot-reload safety: a script WITHOUT `BG` run after a script WITH one must
  not inherit the stale value (serialize globals are reset per exec).

Run directly: `python3 test/background_test.py`
"""

import os
import sys
import tempfile

sys.path.insert(0, ".")
sys.path.insert(0, "test")
from helpers import check, section, summary

from videocode import serialize
from videocode.constants import BACKGROUND_Z_INDEX
from videocode.context import Context


def runScene(source: str) -> None:
    path = tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w")
    path.write(source)
    path.close()
    try:
        serialize.execScene(path.name)
    finally:
        os.remove(path.name)


# ── plain color ──────────────────────────────────────────────────────────────
section("BG = <rgba> — lands in Context.backgroundColor, normalized")

runScene("from videocode import *\nBG = WHITE\nRectangle(width=1, height=1)\n")
check("white -> (1, 1, 1)", Context.backgroundColor == (1.0, 1.0, 1.0))

runScene("from videocode import *\nBG = rgba(51, 102, 204)\nRectangle(width=1, height=1)\n")
check("custom color normalized 0..1", Context.backgroundColor == (0.2, 0.4, 0.8))

# ── absence + hot-reload leak guard ─────────────────────────────────────────
section("no BG — None, and a previous run's BG must not leak in")

runScene("from videocode import *\nRectangle(width=1, height=1)\n")
check("no BG -> None (stale value from the previous exec cleared)", Context.backgroundColor is None)

# ── gradient — auto full-frame background Rectangle ──────────────────────────
section("BG = <gradient> — one full-frame Rectangle, behind everything, frame 0")

runScene("from videocode import *\nBG = LinearGradient(RED, BLUE)\nRectangle(width=1, height=1)\nwait(2)\n")
check("clear color untouched (the gradient is an input, not a clear value)", Context.backgroundColor is None)

# The scene created 1 input; the resolver appended the background rect last
# (a Rectangle serializes as its base "Polygon" create type).
bgIdx = max(Context.stack.keys())
create = Context.stack[bgIdx][-1]
check("background rect appended as a Polygon create entry", create["type"] == "Polygon")
frames = {f: e for f, e in Context.stack[bgIdx].items() if f != -1}
check("visible from frame 0 (noHiding: no auto-Hide entry)",
      not any("Hide" in e for e in frames.values()))
zAtZero = frames.get(0, {}).get("ZIndex", {}).get("args", {}).get("zIndex")
check("layered behind everything from frame 0 (background zIndex sentinel)",
      zAtZero == BACKGROUND_Z_INDEX)

# ── rejected types ───────────────────────────────────────────────────────────
section("BG is color-only — non-colors are rejected")

try:
    runScene("from videocode import *\nBG = 'white'\n")
    check("non-rgba BG raises TypeError", False)
except TypeError:
    check("non-rgba BG raises TypeError", True)

# ── summary ──────────────────────────────────────────────────────────────────
summary()
