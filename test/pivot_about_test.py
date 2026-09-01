#!/usr/bin/env python3

"""
Assertion-based tests for `about` — the pivot placed by the author.

Before this, a group could only ever be turned around a point derived from its
own content: `align(x, y)` is a fraction of the bounding box, so the question
"turn this around the origin" had no answer unless the origin happened to be a
fraction of the box. `about=v2(x, y)` names the point outright.

Contract:
- `about` wins over `align`, and it is a location rather than a question about
  the content — an empty group has one just as much as a full one.
- It rides on the timeline like `align` does: placed after frames have already
  been written, it must NOT reach back and re-pivot them.
- Left alone, every existing behaviour is the one that was there before.

Run directly: `python3 test/pivot_about_test.py`
"""

import sys

sys.path.insert(0, ".")
sys.path.insert(0, "test")
from helpers import check, section, summary

from videocode import *


def pair() -> tuple:
    """Two unit squares, one at the origin and one 2 to its right."""
    a = Rectangle(width=1, height=1)
    b = Rectangle(width=1, height=1)
    b.moveTo(x=2, y=0, duration=0.4)
    return a, b, Group(a, b)


def near(got, want, tol=1e-9) -> bool:
    return abs(got - want) < tol


section("the derived pivot is unchanged when nothing is placed")

a, b, g = pair()
g.rotateBy(90, duration=0.4)
check("box centre (1, 0) is still the default pivot", near(a.meta.position.x, 1.0) and near(a.meta.position.y, 1.0))
check("and the second member mirrors it", near(b.meta.position.x, 1.0) and near(b.meta.position.y, -1.0))

section("about places the pivot outright")

a, b, g = pair()
g.rotateBy(90, about=v2(0.0, 0.0), duration=0.4)
check("the member sitting on the pivot does not move", near(a.meta.position.x, 0.0) and near(a.meta.position.y, 0.0))
check("the other one swings a full radius", near(b.meta.position.x, 0.0, 1e-9) and near(b.meta.position.y, -2.0))

section("about beats align — a location, not a fraction of the box")

a, b, g = pair()
g.alignTo(x=0, y=0, duration=0.4)
a, b, g = pair()
g.rotateBy(90, about=v2(2.0, 0.0), duration=0.4)
check("turning about the right-hand square leaves it where it was", near(b.meta.position.x, 2.0) and near(b.meta.position.y, 0.0))

section("an empty group has a placed pivot even with no content to derive one from")

empty = Group()
placed = empty._pivot(about=v2(3.0, 4.0))
check("_pivot returns the placed point", near(placed.x, 3.0) and near(placed.y, 4.0))
derived = empty._pivot()
check("and still falls back to the origin without one", near(derived.x, 0.0) and near(derived.y, 0.0))

section("placing a pivot does not reach back into frames already written")

a, b, g = pair()
g.rotateBy(90, duration=0.4)
firstHalf = v2(*b.meta.position)
g.rotateBy(90, about=v2(0.0, 0.0), duration=0.4, start=0.4)
opening = g._rigidTimeline[sorted(g._rigidTimeline)[0]]
check("the opening frame says 'no placed pivot here' out loud", opening.get("about.x", "missing") is None)
check("the frames written before it kept the derived pivot", near(firstHalf.x, 1.0) and near(firstHalf.y, -1.0))

section("a leaf turns and scales about the placed point too")

leaf = Rectangle(width=1, height=1)
leaf.moveTo(x=2, y=0, duration=0.4)
leaf.rotateBy(90, about=v2(0.0, 0.0), duration=0.4)
check("it travelled — nothing downstream would have moved it", near(leaf.meta.position.x, 0.0) and near(leaf.meta.position.y, -2.0))
check("and it still spun on itself", near(leaf.meta.rotation, 90.0))

still = Rectangle(width=1, height=1)
still.moveTo(x=2, y=0, duration=0.4)
still.rotateBy(90, duration=0.4)
check("without a placed pivot a leaf turns where it stands", near(still.meta.position.x, 2.0) and near(still.meta.position.y, 0.0))

grown = Rectangle(width=1, height=1)
grown.moveTo(x=2, y=0, duration=0.4)
grown.scaleTo(2, about=v2(0.0, 0.0), duration=0.4)
check("scaling about a point pushes the leaf away from it", near(grown.meta.position.x, 4.0) and near(grown.meta.position.y, 0.0))

oneAxis = Rectangle(width=1, height=1)
oneAxis.moveTo(x=2, y=3, duration=0.4)
oneAxis.scaleTo(x=2, about=v2(0.0, 0.0), duration=0.4)
check("an axis nobody claimed does not drag the leaf along it", near(oneAxis.meta.position.x, 4.0) and near(oneAxis.meta.position.y, 3.0))

section("Text — the anchor grouping After Effects has and this engine did not")


def implied(text: str, mode, degree=180):
    """
    Where each letter turned around, recovered from the motion itself.

    A half-turn about P maps x to 2P - x, so the midpoint of a letter's before
    and after IS the pivot it used — without asking the implementation what it
    thinks it did.
    """
    t = Text(text)
    t.anchor = mode
    before = [v2(*l.meta.position) for l in t.inputs]
    t.rotateBy(degree, duration=0.4)
    after = [v2(*l.meta.position) for l in t.inputs]
    return t, [(round((a.x + b.x) / 2, 9), round((a.y + b.y) / 2, 9)) for a, b in zip(before, after)], before, after


t, pivots, before, after = implied("ab cd", Anchor.WORD)
check("both letters of a word turn around the same point", pivots[0] == pivots[1] and pivots[2] == pivots[3])
check("and the two words do not share it", pivots[0] != pivots[2])

t, pivots, before, after = implied("ab cd", Anchor.ALL)
check("ALL keeps one pivot for the whole text", len(set(pivots)) == 1)

t, pivots, before, after = implied("ab cd", Anchor.CHARACTER)
check("CHARACTER moves nothing — every glyph spins where it stands", all(near(a.x, b.x) and near(a.y, b.y) for a, b in zip(before, after)))
check("while still turning", near(t.inputs[0].meta.rotation, 180.0))

lineWise = implied("ab\ncd", Anchor.LINE)[1]
allWise = implied("ab\ncd", Anchor.ALL)[1]
check("LINE splits a two-line text where ALL does not", len(set(lineWise)) == 2 and len(set(allWise)) == 1)
check("one line of text makes LINE and ALL the same question", implied("abcd", Anchor.LINE)[1] == implied("abcd", Anchor.ALL)[1])

section("about still wins over the anchor grouping")

t = Text("ab cd")
t.anchor = Anchor.CHARACTER
before = [v2(*l.meta.position) for l in t.inputs]
t.rotateBy(180, about=v2(0.0, 0.0), duration=0.4)
after = [v2(*l.meta.position) for l in t.inputs]
check("a placed point is an answer, not a question about the content", all(near(a.x, -b.x) and near(a.y, -b.y) for a, b in zip(before, after)))

section("the emitted frame carries its pivot as a number, never a re-read")

a = Rectangle(width=1, height=1)
b = Rectangle(width=1, height=1)
b.moveTo(x=2, y=0, duration=0.4)
g = Group(a, b)
g.rotateBy(90, duration=0.4)
check("every recorded frame carries one", all("pivot.x" in rec for rec in g._rigidTimeline.values()))

settled = (v2(*a.meta.position), v2(*b.meta.position))
# `width` feeds the DERIVED pivot and nothing else in the orbit, so moving it
# changes the answer `_pivot` would give without touching the arithmetic that
# places a member. Re-emitting used to ask again and get the new answer.
# One member only: widening both symmetrically leaves the midpoint where it
# was, and the probe would pass against the very code it is meant to catch.
g._memberBases[0][1].width = 9.0
g._rigidWritten = ()
g._emitTimeline()
again = (v2(*a.meta.position), v2(*b.meta.position))
check(
    "re-emitting a written window cannot re-pivot it",
    all(near(x.x, y.x, 1e-12) and near(x.y, y.y, 1e-12) for x, y in zip(settled, again)),
)

section("placed vs composite — the axis that actually separates a group from a leaf")

leafInput = Rectangle(width=1, height=1)
groupInput = Group(leafInput)
check("a leaf has a slot of its own in the stack", leafInput.placed and not leafInput.composite)
check("a group has none — what is drawn are the members it moves", groupInput.composite and not groupInput.placed)
check("and a Text carved out of letters is composite too", Text("ab").find("a").inputs[0].composite)

summary()
