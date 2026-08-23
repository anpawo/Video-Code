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

from videocode.edit import (
    argumentSpan,
    callLine,
    findCalls,
    positionalSpan,
    readPositional,
    readArgument,
    removeArgument,
    removeCallSpan,
    setArgument,
)

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

section("argumentSpan — the same edit, as a range the editor can apply")
span = argumentSpan(SOURCE, 10, "rotateBy", "duration", "2.0")
check("a span was given", span is not None)
if span is not None:
    start, end, text = span
    check("splicing it gives the same file", SOURCE[:start] + text + SOURCE[end:] == setArgument(SOURCE, 10, "rotateBy", "duration", "2.0").source)
    check("it replaces the value, nothing more", SOURCE[start:end] == "1.5" and text == "2.0")

span = argumentSpan(SOURCE, 6, "Video", "endFrame", "240")
check("adding one is an insertion", span is not None and span[0] == span[1])
if span is not None:
    start, end, text = span
    check("with its own separator", text == ", endFrame=240")
    check("splicing it gives the same file", SOURCE[:start] + text + SOURCE[end:] == setArgument(SOURCE, 6, "Video", "endFrame", "240").source)

check("the same value is no span at all", argumentSpan(SOURCE, 10, "rotateBy", "duration", "1.5") is None)
check("a call that is not there is refused", argumentSpan(SOURCE, 10, "moveBy", "x", "1") is None)

section("broken source is refused, not mangled")
broken = "square = Square(side=\n"
edit = setArgument(broken, 1, "Square", "side", "2")
check("returned unchanged", edit.source == broken and not edit.changed)

# ── An argument with no name ───────────────────────────────────────────────
section("positionalSpan — `wait(0.3)` writes its seconds without a name")
span = positionalSpan(SOURCE, 8, "wait", 0, "0.6")
check("a span was given", span is not None)
if span is not None:
    start, end, text = span
    check("it replaces the number, nothing more", SOURCE[start:end] == "0.3" and text == "0.6")
    edited = SOURCE[:start] + text + SOURCE[end:]
    check("the line reads as written", line(edited, 8) == "wait(0.6)")
    check("every other line is untouched", untouched(SOURCE, edited, 8))

check("the same value is no span at all", positionalSpan(SOURCE, 8, "wait", 0, "0.3") is None)

empty = "wait()\n"
span = positionalSpan(empty, 1, "wait", 0, "0.5")
check("an argument that is not there yet is appended", span is not None)
if span is not None:
    start, end, text = span
    check("with no stray separator", empty[:start] + text + empty[end:] == "wait(0.5)\n")

check("a slot cannot be skipped", positionalSpan(empty, 1, "wait", 2, "0.5") is None)

section("readPositional — an argument with no name, read back")
check("the file a Video was made from", readPositional(SOURCE, 6, "Video", 0) == '"shot.mp4"')
check("the seconds a wait was given", readPositional(SOURCE, 8, "wait", 0) == "0.3")
check("a slot nothing was written into", readPositional(SOURCE, 8, "wait", 1) is None)
check("a call that is not there", readPositional(SOURCE, 6, "Sound", 0) is None)

# ── Taking a call away ─────────────────────────────────────────────────────
section("removeCallSpan — a link in a chain loses only its link")
span = removeCallSpan(SOURCE, 10, "scaleTo")
check("a span was given", span is not None)
if span is not None:
    start, end, text = span
    edited = SOURCE[:start] + text + SOURCE[end:]
    check("the scale is gone", line(edited, 10) == "Group(square, circle).rotateBy(180, duration=1.5)")
    check("the file still parses", isinstance(compile(edited, "scene.py", "exec"), object))
    check("every other line is untouched", untouched(SOURCE, edited, 10))

span = removeCallSpan(SOURCE, 10, "rotateBy")
check("the middle link goes too, and only it", span is not None)
if span is not None:
    start, end, text = span
    edited = SOURCE[:start] + text + SOURCE[end:]
    check("what is left is the rest of the chain",
          line(edited, 10) == "Group(square, circle).scaleTo(0.5, duration=0.5)")

section("removeCallSpan — a statement of its own takes its line")
alone = "square = Square(side=1)\nsquare.fadeIn()\nsquare.moveBy(x=1)\n"
span = removeCallSpan(alone, 2, "fadeIn")
check("a span was given", span is not None)
if span is not None:
    start, end, text = span
    edited = alone[:start] + text + alone[end:]
    check("the line went with it, newline included",
          edited == "square = Square(side=1)\nsquare.moveBy(x=1)\n")
    check("no bare name left behind", "square\n" not in edited)

section("removeCallSpan — what it refuses")
check("a call that is not there", removeCallSpan(SOURCE, 10, "moveBy") is None)
check("the call that MADE the element", removeCallSpan(SOURCE, 5, "Square") is None)
check("broken source", removeCallSpan("square.fadeIn(\n", 1, "fadeIn") is None)

# ── summary ────────────────────────────────────────────────────────────────
summary()
