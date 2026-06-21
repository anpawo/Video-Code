#!/usr/bin/env python3

"""
Assertion-based smoke tests for LinearGradient / RadialGradient multi-stop
("color breakpoint") support — covers stop normalization/auto-spacing, JSON
serialization shape consumed by the C++ side, and operator behavior (angle
preservation, color math). Run directly: `python3 test/gradient_test.py`
"""

import sys

sys.path.insert(0, ".")
sys.path.insert(0, "test")
from helpers import check, section, summary

from videocode import RED, GREEN, BLUE, WHITE, BLACK, RED_A, RED_B, BLUE_B
from videocode.ty import LinearGradient, RadialGradient, ConicGradient, rgba

def approx(a: float, b: float, eps: float = 1e-6) -> bool:
    return abs(a - b) <= eps

# ── LinearGradient: default 2-stop positions ─────────────────────────────────
section("LinearGradient — 2-stop default positions")
g = LinearGradient(RED, BLUE)
check("first stop at 0%", approx(g.stops[0][1], 0.0))
check("last stop at 100%", approx(g.stops[1][1], 100.0))
check("colors preserved in order", g.stops[0][0] is RED and g.stops[1][0] is BLUE)
check("angle defaults to 0", g.angle == 0)

# ── LinearGradient: pinned stop + auto-spaced neighbors ──────────────────────
section("LinearGradient — pinned stop with auto-spaced first/last")
g = LinearGradient(RED, (GREEN, 30), BLUE, angle=90)
check("3 stops resolved", len(g.stops) == 3)
check("first auto → 0%", approx(g.stops[0][1], 0.0))
check("middle pinned → 30%", approx(g.stops[1][1], 30.0))
check("last auto → 100%", approx(g.stops[2][1], 100.0))
check("angle stored", g.angle == 90)

# ── LinearGradient: auto-distribution ────────────────────────────────────────
section("LinearGradient — auto-distribution between positioned neighbors")
g = LinearGradient(RED, (GREEN, 50), BLUE, WHITE)
check("4 stops resolved", len(g.stops) == 4)
check("RED → 0%", approx(g.stops[0][1], 0.0))
check("GREEN pinned → 50%", approx(g.stops[1][1], 50.0))
check("BLUE evenly spaced → 75%", approx(g.stops[2][1], 75.0))
check("WHITE → 100%", approx(g.stops[3][1], 100.0))

section("LinearGradient — auto-distribution of a run of 3 unpositioned stops")
g = LinearGradient((RED, 0), GREEN, BLUE, WHITE, (BLACK, 100))
positions = [p for _, p in g.stops]
check("evenly spaced quarter-steps", all(approx(p, e) for p, e in zip(positions, [0, 25, 50, 75, 100])))

# ── Monotonic clamping ────────────────────────────────────────────────────────
section("LinearGradient — monotonic clamping of out-of-order pins")
g = LinearGradient((RED, 50), (GREEN, 20), (BLUE, 80))
positions = [p for _, p in g.stops]
check("middle clamped up to predecessor", approx(positions[1], 50.0))
check("non-decreasing overall", all(positions[i] <= positions[i + 1] for i in range(len(positions) - 1)))

# ── Validation ────────────────────────────────────────────────────────────────
section("validation")
for cls in (LinearGradient, RadialGradient, ConicGradient):
    name = cls.__name__
    try:
        cls(RED)
        check(f"{name} rejects single-stop", False)
    except ValueError:
        check(f"{name} rejects single-stop", True)
    try:
        cls()
        check(f"{name} rejects zero-stop", False)
    except ValueError:
        check(f"{name} rejects zero-stop", True)

# ── JSON serialization: LinearGradient ───────────────────────────────────────
section("LinearGradient — jsonSerialization shape")
g = LinearGradient(RED, (GREEN, 30), BLUE, angle=90)
js = g.jsonSerialization()
check("top-level is (stops, angle) pair", isinstance(js, tuple) and len(js) == 2)
stopsJson, angleJson = js
check("stops is a list", isinstance(stopsJson, list) and len(stopsJson) == 3)
check("each stop is ((r,g,b,a), percent)", all(
    isinstance(s, tuple) and len(s) == 2 and isinstance(s[0], tuple) and len(s[0]) == 4
    for s in stopsJson
))
check("percents in 0-100 range", all(0.0 <= s[1] <= 100.0 for s in stopsJson))
check("angle serialized as number", angleJson == 90)

# ── JSON serialization: RadialGradient ───────────────────────────────────────
section("RadialGradient — jsonSerialization shape")
rg = RadialGradient(RED, (WHITE, 40), BLUE)
js = rg.jsonSerialization()
check("top-level is (stops, discriminator) pair", isinstance(js, tuple) and len(js) == 2)
stopsJson, disc = js
check("stops is a list", isinstance(stopsJson, list) and len(stopsJson) == 3)
check("discriminator is 'radial' string", disc == "radial")
check("percents in 0-100 range", all(0.0 <= s[1] <= 100.0 for s in stopsJson))

# ── ConicGradient: default 2-stop positions + angle ──────────────────────────
section("ConicGradient — 2-stop default positions")
g = ConicGradient(RED, BLUE)
check("first stop at 0%", approx(g.stops[0][1], 0.0))
check("last stop at 100%", approx(g.stops[1][1], 100.0))
check("colors preserved in order", g.stops[0][0] is RED and g.stops[1][0] is BLUE)
check("angle defaults to 0", g.angle == 0)

# ── ConicGradient: pinned stop + angle ───────────────────────────────────────
section("ConicGradient — pinned stop with auto-spaced first/last")
g = ConicGradient(RED, (GREEN, 30), BLUE, angle=90)
check("3 stops resolved", len(g.stops) == 3)
check("first auto → 0%", approx(g.stops[0][1], 0.0))
check("middle pinned → 30%", approx(g.stops[1][1], 30.0))
check("last auto → 100%", approx(g.stops[2][1], 100.0))
check("angle stored", g.angle == 90)

# ── JSON serialization: ConicGradient ────────────────────────────────────────
section("ConicGradient — jsonSerialization shape")
cg = ConicGradient(RED, (WHITE, 40), BLUE, angle=90)
js = cg.jsonSerialization()
check("top-level is (stops, discriminator) pair", isinstance(js, tuple) and len(js) == 2)
stopsJson, disc = js
check("stops is a list", isinstance(stopsJson, list) and len(stopsJson) == 3)
check("discriminator is ('conic', angle) pair", isinstance(disc, tuple) and disc[0] == "conic" and disc[1] == 90)
check("percents in 0-100 range", all(0.0 <= s[1] <= 100.0 for s in stopsJson))

# ── LinearGradient operators ──────────────────────────────────────────────────
section("LinearGradient — operators preserve angle and operate per-stop")
base = LinearGradient(RED_B, (GREEN, 30), BLUE_B, angle=45)

orResult = base | 0.5
check("__or__ returns LinearGradient", isinstance(orResult, LinearGradient))
check("__or__ preserves angle", orResult.angle == base.angle)
check("__or__ preserves stop positions", [p for _, p in orResult.stops] == [p for _, p in base.stops])
check("__or__ applies per-stop", orResult.stops[0][0].jsonSerialization() == (base.stops[0][0] | 0.5).jsonSerialization())

other = LinearGradient(WHITE, (WHITE, 30), WHITE, angle=45)

addResult = base + other
check("__add__ returns LinearGradient", isinstance(addResult, LinearGradient))
check("__add__ preserves angle", addResult.angle == base.angle)
check("__add__ applies per-stop", addResult.stops[0][0].jsonSerialization() == (base.stops[0][0] + other.stops[0][0]).jsonSerialization())

subResult = base - other
check("__sub__ returns LinearGradient", isinstance(subResult, LinearGradient))
check("__sub__ preserves angle", subResult.angle == base.angle)
check("__sub__ applies per-stop", subResult.stops[0][0].jsonSerialization() == (base.stops[0][0] - other.stops[0][0]).jsonSerialization())

mulResult = base * 2
check("__mul__ returns LinearGradient", isinstance(mulResult, LinearGradient))
check("__mul__ preserves angle", mulResult.angle == base.angle)
check("__mul__ applies per-stop", mulResult.stops[0][0].jsonSerialization() == (base.stops[0][0] * 2).jsonSerialization())

rmulResult = 2 * base
check("__rmul__ matches __mul__", rmulResult.stops[0][0].jsonSerialization() == mulResult.stops[0][0].jsonSerialization())

# ── RadialGradient operators ──────────────────────────────────────────────────
section("RadialGradient — operators operate per-stop")
rbase = RadialGradient(RED_B, (GREEN, 50), BLUE_B)

orResult = rbase | 0.5
check("__or__ returns RadialGradient", isinstance(orResult, RadialGradient))
check("__or__ preserves stop positions", [p for _, p in orResult.stops] == [p for _, p in rbase.stops])

mulResult = rbase * 2
check("__mul__ returns RadialGradient", isinstance(mulResult, RadialGradient))
check("__mul__ applies per-stop", mulResult.stops[0][0].jsonSerialization() == (rbase.stops[0][0] * 2).jsonSerialization())

# ── ConicGradient operators ───────────────────────────────────────────────────
section("ConicGradient — operators preserve angle and operate per-stop")
cbase = ConicGradient(RED_B, (GREEN, 30), BLUE_B, angle=45)

orResult = cbase | 0.5
check("__or__ returns ConicGradient", isinstance(orResult, ConicGradient))
check("__or__ preserves angle", orResult.angle == cbase.angle)
check("__or__ preserves stop positions", [p for _, p in orResult.stops] == [p for _, p in cbase.stops])
check("__or__ applies per-stop", orResult.stops[0][0].jsonSerialization() == (cbase.stops[0][0] | 0.5).jsonSerialization())

addResult = cbase + WHITE
check("__add__ returns ConicGradient", isinstance(addResult, ConicGradient))
check("__add__ preserves angle", addResult.angle == cbase.angle)
check("__add__ applies per-stop", addResult.stops[0][0].jsonSerialization() == (cbase.stops[0][0] + WHITE).jsonSerialization())

mulResult = cbase * 2
check("__mul__ returns ConicGradient", isinstance(mulResult, ConicGradient))
check("__mul__ preserves angle", mulResult.angle == cbase.angle)
check("__mul__ applies per-stop", mulResult.stops[0][0].jsonSerialization() == (cbase.stops[0][0] * 2).jsonSerialization())

rmulResult = 2 * cbase
check("__rmul__ matches __mul__", rmulResult.stops[0][0].jsonSerialization() == mulResult.stops[0][0].jsonSerialization())

# ── Both are rgba subclasses ──────────────────────────────────────────────────
section("rgba subclassing")
check("LinearGradient is rgba", isinstance(base, rgba))
check("RadialGradient is rgba", isinstance(rbase, rgba))
check("ConicGradient is rgba", isinstance(cbase, rgba))

# ── __str__ / __repr__ ────────────────────────────────────────────────────────
section("string representation")
s = str(base)
check("LinearGradient __str__ mentions angle", "angle=45" in s)
check("LinearGradient __repr__ matches __str__", repr(base) == s)
rs = str(rbase)
check("RadialGradient __str__ has no angle", "angle" not in rs)
check("RadialGradient __repr__ matches __str__", repr(rbase) == rs)
cs = str(cbase)
check("ConicGradient __str__ mentions angle", "angle=45" in cs)
check("ConicGradient __repr__ matches __str__", repr(cbase) == cs)

summary()
