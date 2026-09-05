#!/usr/bin/env python3

"""
`moveAlong(path)` — travelling a curve at one speed, not at its points'.

The points a curve is written with are dense where it bends and sparse where it
runs straight. An object stepping from one to the next therefore crawls through
the corners and bolts down the straights, which is what "follow this path" was
never supposed to mean. The walk is measured first, and every frame is a step
of the same LENGTH along it — the arc-length sampling the roadmap said was the
only missing piece.

Run directly: `python3 test/move_along_test.py`
"""

import sys

sys.path.insert(0, ".")
sys.path.insert(0, "test")
from helpers import check, section, summary

from videocode import Circle, Curve, Easing
from videocode.context import Context
from videocode.serialize import _resetContext
from videocode.template.effect.core.moveAlong import moveAlong


def claimed(inp, key: str, field: str) -> list[float]:
    entry = Context.stack[inp.meta.index]
    return [shader["args"][field]
            for frame, keys in sorted(entry.items()) if frame != -1
            for name, shader in keys.items()
            if name.startswith(key) and shader["args"].get(field) is not None]


# ── One speed, whatever the points ─────────────────────────────────────────
# A straight run from -5 to 5 written with a point 0.1 along it: by points, the
# first step would be a hundredth of the journey and the second the rest.
section("a step is a length, not a point")
_resetContext()
uneven = Curve([(-5, 0), (-4.9, 0), (5, 0)])
dot = Circle(radius=0.3)
dot.moveAlong(uneven, duration=1, easing=Easing.Linear)

xs = claimed(dot, "Position", "x")
gaps = [after - before for before, after in zip(xs, xs[1:])]
check(f"it starts on the path ({xs[0]})", abs(xs[0] + 5) < 1e-6)
check(f"and arrives on its last point ({xs[-1]})", abs(xs[-1] - 5) < 1e-6)
check(f"every step is the same length ({min(gaps):.4f} to {max(gaps):.4f})",
      max(gaps) - min(gaps) < 0.01 * max(gaps))
check("which is not what the points would have given",
      abs(gaps[0] - 0.1) > 0.2)

section("an easing still shapes that speed")
_resetContext()
eased = Circle(radius=0.3)
eased.moveAlong(Curve([(-5, 0), (5, 0)]), duration=1, easing=Easing.InOut)
easedGaps = [after - before for before, after in zip(claimed(eased, "Position", "x"), claimed(eased, "Position", "x")[1:])]
check(f"it leaves slowly and runs in the middle ({easedGaps[0]:.3f} then {max(easedGaps):.3f})",
      easedGaps[0] < max(easedGaps) / 2)

# ── Turned the way it is going ─────────────────────────────────────────────
section("face=True turns it along the path")
_resetContext()
corner = Circle(radius=0.3)
corner.moveAlong(Curve([(-4, 0), (0, 0), (0, 4)]), duration=1, easing=Easing.Linear, face=True)
angles = claimed(corner, "Rotation", "degree")
# A claim is only written where the angle CHANGES — the engine drops a write
# that says what is already true, and the state holds until something says
# otherwise. So a run to the right claims nothing at all (it is facing 0, the
# angle it starts at), and the corner claims the turn.
check(f"nothing is claimed while it runs straight ({len(angles)} claims for 30 frames)", len(angles) == 3)
check(f"the turn ends on a quarter, upward ({angles[-1]:.1f}°)", abs(angles[-1] + 90) < 1e-6)
check(f"and it gets there through the corner, not in one jump ({[round(a, 1) for a in angles]})",
      all(before > after for before, after in zip(angles, angles[1:])))

section("without it, nothing turns")
_resetContext()
straight = Circle(radius=0.3)
straight.moveAlong(Curve([(-4, 0), (0, 4)]), duration=0.5)
check("no rotation is claimed at all", claimed(straight, "Rotation", "degree") == [])

# ── What it refuses ────────────────────────────────────────────────────────
section("what moveAlong refuses")
_resetContext()
for path, why in (([(1, 1)], "a path of one point"), ([(1, 1), (1, 1)], "a path of no length")):
    try:
        list(moveAlong(Circle(radius=0.3), path))
        check(f"{why} is refused", False)
    except ValueError as error:
        check(f"{why} is refused, with a reason ({error})", True)

summary()
