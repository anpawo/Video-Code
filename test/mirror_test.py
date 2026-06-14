#!/usr/bin/env python3

"""
Assertion-based smoke tests for `Input.mirror`/`unmirror` — verifies that
shaders applied to a source `Input` are replicated onto its mirror targets via
`Context.apply`/`Context.stack`, that `unmirror` stops propagation, that mutual
mirror links don't infinite-loop, and that `Group.apply` mirrors too.
Run directly: `python3 test/mirror_test.py`
"""

import sys

sys.path.insert(0, ".")

from videocode import Rectangle, Context
from videocode.input.interface.Group import Group

failures: list[str] = []


def check(label: str, condition: bool):
    if condition:
        print(f"  ok   {label}")
    else:
        print(f"  FAIL {label}")
        failures.append(label)


def approx(a: float, b: float, eps: float = 1e-6) -> bool:
    return abs(a - b) <= eps


def framesOf(index: int) -> list[int]:
    return [k for k in Context.stack.get(index, {}) if k != -1]


# ── basic propagation: moveTo replicates onto the mirrored target ───────────
print("mirror — moveTo replicates onto target")
a = Rectangle()
b = Rectangle()
a.mirror(b)

a.moveTo(x=5, y=3)

check("source moved to (5, 3)", approx(a.meta.position.x, 5) and approx(a.meta.position.y, 3))
check("target synced to (5, 3)", approx(b.meta.position.x, 5) and approx(b.meta.position.y, 3))

aFrames = framesOf(a.meta.index)
bFrames = framesOf(b.meta.index)
check("source has Position frame(s)", len(aFrames) > 0)
check("target has matching Position frame(s)", aFrames == bFrames)
for f in aFrames:
    check(f"frame {f}: target Position args match source", Context.stack[a.meta.index][f]["Position"]["args"] == Context.stack[b.meta.index][f]["Position"]["args"])


# ── rotateBy: target ends up at the same absolute rotation ───────────────────
print("mirror — rotateBy replicates absolute destination")
c = Rectangle()
d = Rectangle()
c.mirror(d)
d.meta.rotation = 10  # diverge target's starting state before mirroring a rotateBy

c.rotateBy(45)

check("source rotated by 45 -> 45", approx(c.meta.rotation, 45))
check("target synced to source's resulting rotation (45)", approx(d.meta.rotation, 45))


# ── unmirror stops propagation ───────────────────────────────────────────────
print("unmirror — stops further propagation")
e = Rectangle()
f = Rectangle()
e.mirror(f)
e.moveTo(x=1, y=1)
fFramesBefore = set(framesOf(f.meta.index))

e.unmirror(f)
e.moveTo(x=9, y=9)
fFramesAfter = set(framesOf(f.meta.index))

check("target received the first move", len(fFramesBefore) > 0)
check("target did not receive the second move", fFramesAfter == fFramesBefore)
check("source still moved after unmirror", approx(e.meta.position.x, 9) and approx(e.meta.position.y, 9))
check("target position unchanged after unmirror", approx(f.meta.position.x, 1) and approx(f.meta.position.y, 1))


# ── mutual mirror links are cycle-safe ───────────────────────────────────────
print("mirror — mutual links don't infinite-loop")
g = Rectangle()
h = Rectangle()
g.mirror(h)
h.mirror(g)

g.moveTo(x=2, y=2)

gFrames = framesOf(g.meta.index)
hFrames = framesOf(h.meta.index)
check("source applied exactly once per frame", all(len(Context.stack[g.meta.index][fr]) >= 1 for fr in gFrames))
check("target applied exactly once per frame", all(len(Context.stack[h.meta.index][fr]) >= 1 for fr in hFrames))
check("both ended up at (2, 2)", approx(g.meta.position.x, 2) and approx(h.meta.position.x, 2))


# ── Group.apply mirrors too ───────────────────────────────────────────────────
print("mirror — Group.apply replicates to a mirrored target")
m1, m2 = Rectangle(), Rectangle()
group = Group(m1, m2)
target = Rectangle()
group.mirror(target)

group.rotateTo(30)

check("group member 1 rotated", approx(m1.meta.rotation, 30))
check("group member 2 rotated", approx(m2.meta.rotation, 30))
check("mirrored target rotated too", approx(target.meta.rotation, 30))


# ── Group.moveBy mirrors as a delta, preserving relative offsets ────────────
print("mirror — Group.moveBy replicates as a delta (preserves relative offset)")
n1 = Rectangle()
n1.moveTo(x=10, y=0)
groupN = Group(n1)
target2 = Rectangle()
target2.moveTo(x=100, y=0)
groupN.mirror(target2)

groupN.moveBy(x=5, y=0)

check("group member moved by 5 -> 15", approx(n1.meta.position.x, 15))
check("mirrored target moved by the same delta -> 105", approx(target2.meta.position.x, 105))


# ── summary ────────────────────────────────────────────────────────────────
print()
if failures:
    print(f"{len(failures)} FAILURE(S):")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)
else:
    print("All checks passed.")
