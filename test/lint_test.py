#!/usr/bin/env python3
"""
`--lint` says what is wrong with a scene without rendering it.

One `file:line: error|warning: message [rule]` per finding, exit 1 on an error:
the scene failing to run (a negative wait is one), a Sound starting on or after
the last frame, a write before frame 0, an element never on screen or only on
the last frame, and the three warnings the editor already showed. The same
findings reach the editor through `execSource`'s warnings, minus
last-frame-only, which is every line typed at the end of a scene until its
wait() is.

The sweep at the end is the guard against a lint that cries wolf: over every
scene of the suite it must find exactly the one true mistake there is.

Run directly: `python3 test/lint_test.py`
"""

import contextlib
import glob
import io
import json
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, ".")
sys.path.insert(0, "test")

from helpers import check, needsRenderer, needsTool, section, summary

from videocode.serialize import execSource, lintSource

NEW_RULES = ("[sound-after-end]", "[before-start]", "[never-visible]", "[last-frame-only]")


def lint(body: str) -> tuple[str, int]:
    return lintSource("from videocode import *\n" + body, "lint_test.py")


def lines(body: str) -> list[str]:
    return lint(body)[0].splitlines()


# ---------------------------------------------------------------------------
section("a scene that does not run is one error line")

text, code = lint("wait(-0.5)\n")
check(f"a negative wait is refused where it is written ({text.strip()})",
      code == 1 and text.count("\n") == 1 and text.startswith("lint_test.py:2: error: ValueError: wait(-0.5)")
      and text.endswith(" [scene-error]\n"))
text, code = lint("Circle(\n")
check("a syntax error too", code == 1 and text.count("\n") == 1 and text.endswith("[scene-error]\n"))

# ---------------------------------------------------------------------------
section("a Sound after the end, or before the start")

check("a Sound starting after the film is an error, said in full",
      lint('wait(1)\nSound("test/test.wav", start=5)\n') == (
          "lint_test.py:3: error: Sound starts at 6.00 s but the film is 1.03 s long, so at most one frame of it is "
          "heard — a Sound does not make the film longer. Add a wait() after it. [sound-after-end]\n", 1))
said = lines('wait(1)\nSound("test/test.wav")\n')
check("so is one on the last frame", len(said) == 1 and "Sound starts at 1.00 s but the film is 1.03 s long" in said[0])
for body in ('wait(1)\nSound("test/test.wav")\nwait(0.5)\n', 'Square()\nSound("test/test.wav")\n',
             'wait(3)\nSound("test/test.wav", start=-1)\nwait(3)\n'):
    check(f"silent: {body!r}", lint(body) == ("", 0))
said = lines('Sound("test/test.wav", start=-2)\nwait(3)\n')
check("a negative delay is its own error, and only that",
      len(said) == 1 and said[0].startswith("lint_test.py:2: error: Sound starts at -2.00 s, before the film does")
      and said[0].endswith("[before-start]"))

# ---------------------------------------------------------------------------
section("a write before frame 0")

check("moveTo(start=-1) loses its first second, and says so",
      lint("s = Square()\ns.moveTo(x=2, start=-1)\nwait(1)\n") == (
          "lint_test.py:3: error: moveTo() starts at frame -30, before the film's first frame — the renderer skips "
          "every frame below 0, so that part never plays. [before-start]\n", 1))
check("a value the bounds check refused is said once",
      lint("s = Square()\ns.hide(start=-1)\nwait(1)\n") == ("lint_test.py:3: error: hide(start=-1): sec is ≥ 0 [bad-value]\n", 1))
said = lines("s = Square()\ns.fadeIn(start=-1)\nwait(1)\n")
check(f"fadeIn(start=-1) gives two true lines ({len(said)})",
      len(said) == 2 and said[0].startswith("lint_test.py:2: warning: Square is never on screen") and said[0].endswith("[never-visible]")
      and said[1].startswith("lint_test.py:3: error: fadeIn() starts at frame -30") and said[1].endswith("[before-start]"))

# ---------------------------------------------------------------------------
section("never on screen, or only on the last frame")

check("opacity(0) and nothing after is a warning, exit 0",
      lint("Circle().opacity(0)\nwait(1)\n") == (
          "lint_test.py:2: warning: Circle is never on screen — hidden or at opacity 0 on every frame. [never-visible]\n", 0))
said = lines('Text("hello").hide()\nwait(1)\n')
check("a Text is one finding, not one per glyph", len(said) == 1 and "Text (5 elements) is never on screen" in said[0])
said = lines("for _ in range(3):\n    Circle().opacity(0)\nwait(1)\n")
check("a loop's elements are one finding at their line", len(said) == 1 and said[0].startswith("lint_test.py:3:") and "Circle (3 elements)" in said[0])
said = lines("with shot() as a:\n    Square()\nwith shot() as b:\n    Circle()\n    wait(1)\ncut(a, b)\n")
check(f"an empty shot's element is never seen ({said})",
      len(said) == 1 and said[0].startswith("lint_test.py:3: warning: Square is never on screen"))
for body in ("s = Square().hide()\nwait(1)\ns.show()\nwait(1)\n", "s = Square().opacity(0)\ns.fadeIn()\nwait(1)\n",
             "with shot() as a:\n    Square()\n    wait(1)\nwith shot() as b:\n    Circle()\n    wait(1)\ncut(a, b, crossfade=0.5)\n",
             'Text("a b c")\nwait(1)\n', "a = Square()\nb = Circle()\nComposition(a, b).fadeIn()\nwait(1)\n",
             "Camera()\nSquare()\nwait(1)\n"):
    found = [line for line in lines(body) if line.endswith(NEW_RULES)]
    check(f"silent: {body!r}", not found)
check("made after the last wait(): on screen one frame",
      lint("wait(2)\nCircle()\n") == (
          "lint_test.py:3: warning: Circle first appears on the film's last frame (60), so it is on screen for one "
          "frame — add a wait() after it. [last-frame-only]\n", 0))
check("with a wait() after it, silent", lint("wait(2)\nCircle()\nwait(1)\n") == ("", 0))
check("a one-frame still is not that", lint("Square()\n") == ("", 0))

# ---------------------------------------------------------------------------
section("the warnings the editor showed now reach the command line")

check("a value out of bounds", lint("s = Square()\ns.opacity(300)\n") == ("lint_test.py:3: error: opacity(o=300): uint8 is 0–255 [bad-value]\n", 1))
text, code = lint("s = Square(side=1)\ns.moveBy(x=1, duration=1)\ns.moveBy(x=-1, duration=1)\n")
check("two lines on one channel", code == 0 and text.count("\n") == 1 and text.startswith("lint_test.py:4: warning:")
      and text.endswith("[contended-key]\n"))

out, err = io.StringIO(), io.StringIO()
with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
    contended = lint("s = Square(side=1)\ns.moveBy(x=1, duration=1)\ns.moveBy(x=-1, duration=1)\n")
    printed = lint('print("hi")\nSquare()\n')
check("nothing else is printed: findings only", out.getvalue() == "" and err.getvalue() == "" and "hi" not in printed[0])

# ---------------------------------------------------------------------------
section("the editor gets the same findings, through the channel it already reads")

report = execSource("from videocode import *\nCircle().opacity(0)\nwait(1)\n", "lint_test.py")
check(f"never-visible is a warning on its line ({report['warnings']})", json.loads(report["warnings"]) == [
    {"line": 1, "sourceLine": 2, "input": 0, "file": "lint_test.py",
     "message": "Circle is never on screen — hidden or at opacity 0 on every frame.", "severity": 2, "rule": "never-visible"}])
check("last-frame-only is not", json.loads(execSource("from videocode import *\nwait(2)\nCircle()\n", "lint_test.py")["warnings"]) == [])
scene = json.loads(execSource("from videocode import *\nCircle().opacity(0)\nSquare()\nwait(1)\n", "lint_test.py")["scene"])
check("the model says which element is ever seen", [e["seen"] for e in scene["elements"]] == [False, True])
check("and its top level is unchanged", set(scene) == {"fps", "frames", "elements", "waits", "markers"})

work = tempfile.mkdtemp(prefix="vc-lint-")
with open(f"{work}/helper_mod.py", "w") as f:
    f.write("from videocode import *\ndef ghost():\n    return Circle().opacity(0)\n")
scenePath = f"{work}/scene.py"
source = "from videocode import *\nfrom helper_mod import ghost\nghost()\nwait(1)\n"
check("a helper module's finding is on the command line, at the helper's line",
      f"{work}/helper_mod.py:3: warning: Circle is never on screen" in lintSource(source, scenePath)[0])
check("and not in the code pane, which shows the open file", json.loads(execSource(source, scenePath)["warnings"]) == [])

# ---------------------------------------------------------------------------
section("no false positive on the scenes of the suite")

scenes = sorted(glob.glob("test/visual/scenes/*.py")) + sorted(glob.glob("docs/atp/scenes/*.py"))
if not needsTool("latex", "mathtex.py renders TeX"):
    scenes = [p for p in scenes if not p.endswith("mathtex.py")]
failed, kept = [], set()
for path in scenes:
    with open(path) as f:
        text, _ = lintSource(f.read(), path)
    failed += [line for line in text.splitlines() if line.endswith("[scene-error]")]
    kept |= {line for line in text.splitlines() if line.endswith(NEW_RULES)}
check(f"every one of the {len(scenes)} scenes runs ({failed[:2]})", not failed)
check(f"the one true mistake among them is found, and nothing else ({sorted(kept)})", kept == {
    "test/visual/scenes/sound.py:10: error: Sound starts at 1.00 s but the film is 0.03 s long, so at most one frame of "
    "it is heard — a Sound does not make the film longer. Add a wait() after it. [sound-after-end]"})

# ---------------------------------------------------------------------------
if needsRenderer("--lint is a flag of the renderer"):
    section("the command line")

    def run(path: str) -> subprocess.CompletedProcess:
        return subprocess.run(["./video-code", "--lint", "--file", path], capture_output=True, text=True)

    said = run("test/visual/scenes/sound.py")
    check(f"a finding: exit 1, the line on stdout, nothing on stderr (rc {said.returncode})",
          said.returncode == 1 and said.stdout.startswith("test/visual/scenes/sound.py:10: error:") and said.stderr == "")
    said = run("test/visual/scenes/shapes.py")
    check("a clean scene: exit 0, nothing printed", said.returncode == 0 and said.stdout == "" and said.stderr == "")
    said = run("/nonexistent.py")
    check("a file that cannot be read", said.returncode == 1 and said.stderr == "--lint: cannot read /nonexistent.py\n")
    broken = os.path.join(work, "broken.py")
    with open(broken, "w") as f:
        f.write("from videocode import *\nwait(-1)\n")
    said = run(broken)
    check("a scene that does not run", said.returncode == 1 and said.stdout.strip().endswith("[scene-error]"))

summary()
