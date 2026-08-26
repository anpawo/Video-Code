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

    # Resolved with carry, because an entry only carries the channels its effect
    # CLAIMED — `position(x=-1)` leaves y as None, and the value that renders is
    # the one the channel last held. See test/composition_test.py.
    out: dict[int, tuple[float, float]] = {}
    x, y = 0.0, 0.0
    for f in sorted(k for k in Context.stack[0] if k != -1):
        args = Context.stack[0][f].get("Position")
        if args is not None:
            claimed = args["args"]
            x = claimed["x"] if claimed["x"] is not None else x
            y = claimed["y"] if claimed["y"] is not None else y
        out[f] = (x, y)
    return out


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

# ── A group inside a group ─────────────────────────────────────────────────
# The bug this guards: `Group(Group(a, b), c).rotateBy(90)` left three squares
# 1 / 0.707 / 1.581 apart that had started 1 / 1 / 2 apart — the formation came
# apart mid-turn. Two causes, both of them "a group is not where it says it
# is": the pivot was sampled from members the rotation had already moved, and
# the parent handed its child an absolute position, which a child reads as a
# displacement from its own pivot.
#
# The assertion is stronger than rigidity, and deliberately so: however the
# members are bracketed, it has to be the SAME animation. Rigidity alone would
# still pass with the turn happening around the wrong point.
section("Group — a group inside a group moves like one flat group")


def trajectories(line: str, n: int) -> list[dict[int, tuple[float, float]]]:
    """Every position each of the first `n` squares is given, by frame."""
    source = (
        "from videocode import *\n"
        "a = Square(side=0.4).position(x=-1)\n"
        "b = Square(side=0.4).position(x=0)\n"
        "c = Square(side=0.4).position(x=1)\n"
        "d = Square(side=0.4).position(x=2)\n" + line + "\nwait(1)\n"
    )
    execSource(source, "group_test_nested.py")

    # Resolved with carry — see `orbit()` above: an entry only carries the
    # channels its effect claimed.
    tracks: list[dict[int, tuple[float, float]]] = []
    for i in range(n):
        out: dict[int, tuple[float, float]] = {}
        x, y = 0.0, 0.0
        for f in sorted(k for k in Context.stack[i] if k != -1):
            args = Context.stack[i][f].get("Position")
            if args is not None:
                claimed = args["args"]
                x = claimed["x"] if claimed["x"] is not None else x
                y = claimed["y"] if claimed["y"] is not None else y
            out[f] = (x, y)
        tracks.append(out)
    return tracks


def sameAsFlat(nested: str, flat: str, n: int) -> float:
    """
    The worst distance between the two bracketings, over every frame either wrote.

    Compared as CURVES, since a position holds until the next one is written: a
    frame one side left out is the value it last wrote. The two do differ in
    WHICH frames they write — carrying a displacement through a level of
    nesting leaves a member sitting exactly on the pivot with a string of 1e-16
    entries that `autodestroy` cannot tell are no-ops — and that is not a
    difference in the animation.
    """

    def at(track: dict[int, tuple[float, float]], f: int) -> tuple[float, float]:
        return track[max(k for k in track if k <= f)]

    worst = 0.0
    for a, b in zip(trajectories(nested, n), trajectories(flat, n)):
        # From where BOTH have started. A member sitting on its construction
        # value writes nothing until something moves it, and the two bracketings
        # need not fall silent on the same frames — before either has spoken,
        # both are where the source put them, which is the same place.
        begin = max(min(a), min(b))
        for f in sorted(set(a) | set(b)):
            if f < begin:
                continue
            worst = max(worst, math.dist(at(a, f), at(b, f)))
    return worst


for what, nestedLine, flatLine, members in (
    ("rotate", "Group(Group(a, b), c).rotateBy(90, duration=1.0)", "Group(a, b, c).rotateBy(90, duration=1.0)", 3),
    ("rotate, nested on the right", "Group(a, Group(b, c)).rotateBy(90, duration=1.0)", "Group(a, b, c).rotateBy(90, duration=1.0)", 3),
    ("scale", "Group(Group(a, b), c).scaleTo(2, duration=1.0)", "Group(a, b, c).scaleTo(2, duration=1.0)", 3),
    ("move", "Group(Group(a, b), c).moveBy(x=2, y=1, duration=1.0)", "Group(a, b, c).moveBy(x=2, y=1, duration=1.0)", 3),
    ("rotate, three levels deep", "Group(Group(Group(a, b), c), d).rotateBy(90, duration=1.0)", "Group(a, b, c, d).rotateBy(90, duration=1.0)", 4),
):
    check(f"{what}: nested == flat, every member, every frame", sameAsFlat(nestedLine, flatLine, members) < 1e-9)

# The failure as it was first seen, in the numbers it was seen in.
ended = [t[max(t)] for t in trajectories("Group(Group(a, b), c).rotateBy(90, duration=1.0)", 3)]
check(
    "the formation is still 1 / 1 / 2 apart at the end of the turn",
    approx(math.dist(ended[0], ended[1]), 1.0)
    and approx(math.dist(ended[1], ended[2]), 1.0)
    and approx(math.dist(ended[0], ended[2]), 2.0),
)

# ── summary ────────────────────────────────────────────────────────────────
summary()
