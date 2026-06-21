#!/usr/bin/env python3

"""
Assertion-based smoke tests for `Group` (#63): broadcast, apply() propagation,
moveTo/moveBy preserving relative layout, waitForOthers, and scaleBy behavior.
Run directly: `python3 test/group_test.py`
"""

import sys

sys.path.insert(0, ".")
sys.path.insert(0, "test")
from helpers import check, section, summary

from videocode import Rectangle, Circle, Context
from videocode.input.interface.Group import Group

def approx(a: float, b: float, eps: float = 1e-6) -> bool:
    return abs(a - b) <= eps

# ── Group: wraps inputs, broadcasts apply ────────────────────────────────────
section("Group — wraps inputs and broadcasts apply()")
a, b = Rectangle(), Rectangle()
group = Group(a, b)

check("group.inputs contains both members", group.inputs == [a, b])

group.rotateTo(30)
check("member 1 rotated", approx(a.meta.rotation, 30))
check("member 2 rotated", approx(b.meta.rotation, 30))
check("member 1 has a Rotation entry on the stack", any("Rotation" in entry for f, entry in Context.stack[a.meta.index].items() if f != -1))

# ── Group.moveTo: relative layout preserved ──────────────────────────────────
section("Group.moveTo — members move together, relative offsets preserved")
m1 = Rectangle().position(x=-1, y=0)
m2 = Rectangle().position(x=1, y=0)
g = Group(m1, m2)

g.moveTo(x=10, y=5)

check("member 1 shifted to (9, 5)", approx(m1.meta.position.x, 9) and approx(m1.meta.position.y, 5))
check("member 2 shifted to (11, 5)", approx(m2.meta.position.x, 11) and approx(m2.meta.position.y, 5))
check("relative offset preserved (2 apart)", approx(m2.meta.position.x - m1.meta.position.x, 2))

# ── Group.moveBy: every member shifts by the same delta ─────────────────────
section("Group.moveBy — every member shifts by the same delta")
n1 = Rectangle().position(x=0, y=0)
n2 = Rectangle().position(x=5, y=5)
g2 = Group(n1, n2)

g2.moveBy(x=2, y=-1)

check("member 1 shifted by (2, -1)", approx(n1.meta.position.x, 2) and approx(n1.meta.position.y, -1))
check("member 2 shifted by (2, -1)", approx(n2.meta.position.x, 7) and approx(n2.meta.position.y, 4))

# ── Group.waitForOthers ───────────────────────────────────────────────────────
section("Group.waitForOthers — all members synced to the latest lastAffectedFrame")
w1, w2 = Rectangle(), Rectangle()
w1.wait(1)  # advances w1's lastAffectedFrame well past w2's
wg = Group(w1, w2)

wg.waitForOthers()

check("both members share the same lastAffectedFrame", w1.meta.lastAffectedFrame == w2.meta.lastAffectedFrame)
check("synced to the max (w1's)", w2.meta.lastAffectedFrame == w1.meta.lastAffectedFrame)

# ── Group.scaleBy: applies delta on top of each member's own base ────────────
# See test/visual/scenes/stateful_group_scale.py for the visual version.
section("Group.scaleBy — applies group delta on top of each member's snapshotted base")
rectS = Rectangle(width=1, height=1).scale(1.5)
circS = Circle(radius=0.5).scale(0.5)
g3 = Group(rectS, circS)

g3.scaleBy(x=0.5, y=0.5, duration=0.2)

check("rect ends at 1.5 + 0.5 = 2.0", approx(rectS.meta.scale.x, 2.0))
check("circle ends at 0.5 + 0.5 = 1.0", approx(circS.meta.scale.x, 1.0))
check("original 1.0 divergence preserved", approx(rectS.meta.scale.x - circS.meta.scale.x, 1.0))

# ── summary ────────────────────────────────────────────────────────────────
summary()
