#!/usr/bin/env python3

"""
Assertion-based tests for `Polygon.open` — the flag that is BOTH a cppAttr and
a geometry rebuild.

Contract:
- At creation, `open` travels in the creation args like any other cppAttr,
  in the same position it has always had (the C++ side reads a dict, but a
  reordering would churn every serialized stack for nothing).
- Assigning it after creation emits `Args:open` to C++ AND rebuilds the
  control points: a closed path lays out 4 points per corner, an open one
  lays out anchor-handle pairs per segment. Sending the flag without the
  points left C++ told it was open while holding closed-path geometry.
- A `prop` stores under `_open`, which is why the creation args are collected
  through the descriptor rather than straight out of `__dict__`.

Run directly: `python3 test/polygon_open_test.py`
"""

import sys

sys.path.insert(0, ".")
sys.path.insert(0, "test")
from helpers import check, section, summary

from videocode import *
from videocode.context import Context


section("creation — open is a cppAttr and stays where it was")

r = Rectangle(width=2, height=2)
creation = Context.stack[0][-1]["args"]
check("open travels in the creation args", creation.get("open") is False)
check(
    "creation args keep their order",
    list(creation.keys()) == ["fillColor", "strokeColor", "strokeWidth", "open", "contourSizes", "points"],
)

section("assignment — the flag reaches C++ and the geometry follows it")

closed = list(r.points)
r.open = True
check("the python side reads back the new value", r.open is True)
check("the points were rebuilt", list(r.points) != closed)
check("an open path is not laid out as 4 points per corner", len(r.points) != len(closed))
check("C++ is told the flag changed", "Args:open" in Context.stack[0][0])
check("C++ is told the points changed in the same breath", "Args:points" in Context.stack[0][0])

section("idempotence — assigning the same value rebuilds nothing")

before = list(r.points)
r.open = True
check("re-assigning True leaves the points alone", list(r.points) == before)

summary()
