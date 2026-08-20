#!/usr/bin/env python3

"""
Assertion-based smoke tests for `Group` (#63): broadcast, apply() propagation,
moveTo/moveBy preserving relative layout, waitForOthers, and scaleBy behavior.
Run directly: `python3 test/group_test.py`
"""

import math
import sys

sys.path.insert(0, ".")
sys.path.insert(0, "test")
from helpers import check, section, summary

from videocode import Rectangle, Circle, Context
from videocode.input.interface.Group import Group
from videocode.serialize import execSource

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

# ── Chained rigid animations of different lengths ──────────────────────────
# A member's position depends on the group's position AND rotation AND scale at
# that frame. The passes are written one after another while the frames they
# cover overlap, so the order they are WRITTEN in must not change the result.
#
# The bug this guards: `rotateBy(180, duration=1.5).scaleTo(0.5, duration=0.5)`
# emitted 45 frames of orbit at scale 1, and the scale pass only corrected the
# 15 frames it covered. The members shrank for half a second and then jumped
# back out to twice the radius in one frame. Writing the same two the other way
# round was fine, which is why the showcase scene never caught it.
section("Group — chaining rigid animations of different lengths, either order")


def orbit(line: str) -> dict[int, tuple[float, float]]:
    """Every position the first member is given, by frame."""
    source = (
        "from videocode import *\n"
        "s = Square(side=1.5).position(x=-1)\n"
        "c = Circle(radius=0.75).position(x=1)\n"
        "wait(0.3)\n" + line + "\nwait(0.5)\n"
    )
    # Through the same door a scene comes in by, which resets the context for us.
    execSource(source, "group_test_scene.py")
    frames = Context.stack[0]
    return {
        f: (entry["Position"]["args"]["x"], entry["Position"]["args"]["y"])
        for f, entry in frames.items()
        if f != -1 and "Position" in entry
    }


def sameAnimation(first: str, second: str) -> float:
    """The worst distance between the two orders, over every frame either wrote."""
    a, b = orbit(first), orbit(second)
    worst = 0.0
    for f in set(a) | set(b):
        if f not in a or f not in b:
            return float("inf")
        worst = max(worst, math.dist(a[f], b[f]))
    return worst


check(
    "rotate(1.5) then scale(0.5) == scale(0.5) then rotate(1.5)",
    sameAnimation(
        "Group(s, c).rotateBy(180, duration=1.5).scaleTo(0.5, duration=0.5)",
        "Group(s, c).scaleTo(0.5, duration=0.5).rotateBy(180, duration=1.5)",
    )
    < 1e-9,
)

check(
    "move(1.5) then scale(0.4) == scale(0.4) then move(1.5)",
    sameAnimation(
        "Group(s, c).moveBy(x=1, duration=1.5).scaleTo(0.5, duration=0.4)",
        "Group(s, c).scaleTo(0.5, duration=0.4).moveBy(x=1, duration=1.5)",
    )
    < 1e-9,
)

check(
    "rotate(1.0) then move(0.3) == move(0.3) then rotate(1.0)",
    sameAnimation(
        "Group(s, c).rotateBy(90, duration=1.0).moveBy(y=1, duration=0.3)",
        "Group(s, c).moveBy(y=1, duration=0.3).rotateBy(90, duration=1.0)",
    )
    < 1e-9,
)

# The jump itself, named: the orbit a member rides must not change radius
# between two frames once the scale that set it has landed.
radii = [math.hypot(x, y) for _, (x, y) in sorted(
    orbit("Group(s, c).rotateBy(180, duration=1.5).scaleTo(0.5, duration=0.5)").items()
)]
check(
    "the orbit never jumps once the scale has landed",
    all(abs(a - b) < 0.2 for a, b in zip(radii, radii[1:])),
)

# ── summary ────────────────────────────────────────────────────────────────
summary()
