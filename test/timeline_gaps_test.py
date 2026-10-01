#!/usr/bin/env python3
"""
A gap's label starts where its gap starts, and no two labels share a spot.

Five gaps a few tenths apart, which is the shape that broke it: counted from
their neighbours, four of the five landed on the same row and were printed one
over the next. Asked of a windowless editor — where each label is drawn, in the
window's frame. No window opens.

Run directly: `python3 test/timeline_gaps_test.py`
"""

import json
import os
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, ".")
sys.path.insert(0, "test")

from helpers import check, needsRenderer, section, summary

if not needsRenderer("the labels are the chrome's"):
    summary()
    sys.exit(0)

SCENE = "test/timeline_gaps/scene.py"
SOCKET = f"/tmp/videocode-gaps-{os.getpid()}.sock"
log = tempfile.NamedTemporaryFile(suffix=".log", delete=False)
dock = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
shot = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
dock.close()
shot.close()
env = {**os.environ, "VC_SOCKET": SOCKET, "VC_DOCK_FILE": dock.name}

# Every label, as [text, left, top, width, height] in the window's frame.
STAMPS = ("JSON.stringify((function(){ const out = [] ; function f(it) { for (const c of it.children) f(c) ; "
          "if (it.text !== undefined && String(it.text).indexOf('wait ') === 0) "
          "{ const chip = it.parent ; const p = chip.mapToItem(null, 0, 0) ; out.push([String(it.text), p.x, p.y, chip.width, chip.height]) } } "
          "f(timeline) ; return out })())")


def tell(*args: str) -> dict:
    run = subprocess.run(["./video-code", "tell", *args], env=env, capture_output=True, text=True, timeout=60)
    try:
        return json.loads(run.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        return {"ok": False}


def probe(expression: str):
    tell("key", f"spec=Eval:{expression}")
    with open(log.name) as out:
        said = out.read()
    answers = [one for one in said.splitlines() if one.startswith("Probed the expression")]
    if not answers:
        raise AssertionError(f"the editor did not answer the probe `{expression}`.\nWhat it said instead:\n{said[-3000:] or '(nothing at all)'}")
    return json.loads(answers[-1][len("Probed the expression ") + len(expression) + 3 :])[0]


editor = subprocess.Popen(["./video-code", "--editor", "--check-chrome", "--serve", "--file", SCENE],
                          env=env, stdout=log, stderr=subprocess.STDOUT)
try:
    deadline = time.time() + 30
    while time.time() < deadline and not tell("state").get("ok"):
        time.sleep(0.5)
    tell("screenshot", f"out={shot.name}")

    pps = probe("timeline.pxPerSecond")
    x0 = 700 - probe("timeline.timeAtWindow(700, 700)") * pps
    gaps = json.loads(probe("JSON.stringify(liveScene.waits)"))
    stamps = json.loads(probe(STAMPS))

    section("a gap's label")
    check(f"every gap has one ({len(stamps)} labels for {len(gaps)} gaps)", len(stamps) == len(gaps) == 5)

    def meet(a: list, b: list) -> bool:
        return a[1] < b[1] + b[3] and b[1] < a[1] + a[3] and a[2] < b[2] + b[4] and b[2] < a[2] + a[4]

    over = [(a[0], b[0]) for i, a in enumerate(stamps) for b in stamps[i + 1:] if meet(a, b)]
    check(f"no two are printed on the same spot ({over or 'none meet'})", not over)

    off = [(stamp[0], round(stamp[1] - (x0 + gap["at"] * pps), 1)) for stamp, gap in zip(stamps, gaps)]
    check(f"each starts where its gap starts ({off})", all(abs(by) < 1 for _, by in off))

    tell("quit")
    editor.wait(timeout=10)
finally:
    if editor.poll() is None:
        editor.kill()
    for path in (SOCKET, log.name, dock.name, shot.name):
        if os.path.exists(path):
            os.unlink(path)

summary()
