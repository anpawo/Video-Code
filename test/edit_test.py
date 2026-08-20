#!/usr/bin/env python3

"""
Assertion-based tests for `videocode/edit.py` — the layer every gesture in the
editor writes through. What it guarantees is narrow and absolute: the value asked
for changes, and NOTHING else in the file does.
Run directly: `python3 test/edit_test.py`
"""

import sys

sys.path.insert(0, ".")
sys.path.insert(0, "test")
from helpers import check, section, summary

from videocode.edit import callLine, findCalls, readArgument, removeArgument, setArgument

SOURCE = '''#!/usr/bin/env python3

from videocode import *

square = Square(side=1.5, fillColor=BLUE_C).position(x=-1)
clip = Video("shot.mp4", startFrame=10)  # keep the comment

wait(0.3)

Group(square, circle).rotateBy(180, duration=1.5).scaleTo(0.5, duration=0.5)
'''


def line(source: str, number: int) -> str:
    return source.splitlines()[number - 1]


def untouched(before: str, after: str, except_: int) -> bool:
    """Every line but one is byte for byte what it was."""
    a, b = before.splitlines(), after.splitlines()
    if len(a) != len(b):
        return False
    return all(x == y for i, (x, y) in enumerate(zip(a, b), start=1) if i != except_)


# ── Reading a chain ─────────────────────────────────────────────────────────
section("findCalls — a chain, in the order it is written")
check("three links, left to right", findCalls(SOURCE, 10) == ["Group", "rotateBy", "scaleTo"])
check("a line with one call", findCalls(SOURCE, 8) == ["wait"])
check("a line with none", findCalls(SOURCE, 2) == [])

section("readArgument — the text, not the value")
check("rotateBy's duration", readArgument(SOURCE, 10, "rotateBy", "duration") == "1.5")
check("scaleTo's own duration", readArgument(SOURCE, 10, "scaleTo", "duration") == "0.5")
check("an argument that is not written", readArgument(SOURCE, 10, "rotateBy", "easing") is None)
check("a call that is not there", readArgument(SOURCE, 10, "moveBy", "x") is None)

# ── Writing ────────────────────────────────────────────────────────────────
section("setArgument — replacing a value")
edit = setArgument(SOURCE, 10, "rotateBy", "duration", "2.0")
check("it changed", edit.changed)
check("the right link of the chain", "rotateBy(180, duration=2.0)" in line(edit.source, 10))
check("the other link kept its own", "scaleTo(0.5, duration=0.5)" in line(edit.source, 10))
check("every other line is untouched", untouched(SOURCE, edit.source, 10))

section("setArgument — adding one that was not there")
edit = setArgument(SOURCE, 6, "Video", "endFrame", "240")
check("written inside the call", 'Video("shot.mp4", startFrame=10, endFrame=240)' in line(edit.source, 6))
check("the trailing comment survives", line(edit.source, 6).endswith("# keep the comment"))
check("every other line is untouched", untouched(SOURCE, edit.source, 6))

section("setArgument — a call with nothing in it yet")
bare = "square.moveBy()\n"
edit = setArgument(bare, 1, "moveBy", "x", "-1")
check("no stray separator", edit.source == "square.moveBy(x=-1)\n")

section("setArgument — the same value is not an edit")
edit = setArgument(SOURCE, 10, "rotateBy", "duration", "1.5")
check("nothing to do", not edit.changed and edit.source == SOURCE)

section("setArgument — a call that is not on that line")
edit = setArgument(SOURCE, 10, "moveBy", "x", "1")
check("refused rather than guessed", not edit.changed and edit.source == SOURCE)
check("and it says why", "no call named" in edit.message)

section("removeArgument — back to the default")
edit = removeArgument(SOURCE, 6, "Video", "startFrame")
check("the argument is gone", 'Video("shot.mp4")' in line(edit.source, 6))
check("no dangling comma", ", )" not in line(edit.source, 6) and "(, " not in line(edit.source, 6))
check("every other line is untouched", untouched(SOURCE, edit.source, 6))

edit = removeArgument(SOURCE, 10, "scaleTo", "duration")
check("removing the only argument of a link", "scaleTo(0.5)" in line(edit.source, 10))

section("callLine — finding a call by name")
check("the Video", callLine(SOURCE, "Video") == 6)
check("the first wait", callLine(SOURCE, "wait") == 8)
check("one that is not there", callLine(SOURCE, "nope") == 0)

# ── What a gesture actually does, end to end ───────────────────────────────
section("a gesture: trimming a video writes its frame range")
trimmed = setArgument(SOURCE, 6, "Video", "startFrame", "30").source
trimmed = setArgument(trimmed, 6, "Video", "endFrame", "300").source
check("both ends written", 'Video("shot.mp4", startFrame=30, endFrame=300)' in line(trimmed, 6))
check("the file still parses", isinstance(compile(trimmed, "scene.py", "exec"), object))
check("nothing else moved", untouched(SOURCE, trimmed, 6))

section("a gesture: moving an effect writes its start")
moved = setArgument(SOURCE, 10, "scaleTo", "start", "0.8").source
check("start added to the right link", "scaleTo(0.5, duration=0.5, start=0.8)" in line(moved, 10))
check("the file still parses", isinstance(compile(moved, "scene.py", "exec"), object))

section("broken source is refused, not mangled")
broken = "square = Square(side=\n"
edit = setArgument(broken, 1, "Square", "side", "2")
check("returned unchanged", edit.source == broken and not edit.changed)

# ── summary ────────────────────────────────────────────────────────────────
summary()
