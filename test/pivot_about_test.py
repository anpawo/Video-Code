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

summary()
