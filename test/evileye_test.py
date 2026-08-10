#!/usr/bin/env python3

"""
Assertion-based tests for the math-shader p[] contract, through evilEye.

The slot each uniform lands in is decided by its NAME (alphabetical), after a
fixed 3-float head: the resolved origin (2) and unit (1), which
resolveEffectParams patches over what pushMathParams sent. That is invisible
from the GLSL side — rename an arg and the shader keeps compiling while reading
the wrong value. These checks rebuild the layout the C++ will send and compare
it against the `// p[N] = name` header the .glsl documents itself with.
Run directly: `python3 test/evileye_test.py`
"""

import re
import sys

sys.path.insert(0, ".")
sys.path.insert(0, "test")
from helpers import check, section, summary

from videocode import evilEye, rgba, starNest
from videocode.shader.fragmentShader.evilEye import EVIL_EYE_GLSL
from videocode.shader.fragmentShader.mathShader import mathShader

# The fixed head, as the GLSL sees it: originX/originY/originUnit go in,
# (originU, originV, unit) come out — same three slots, resolved in place.
HEAD = ["origin", "origin", "unit"]
# Consumed out-of-band by IFragmentShader::isMathHeadArg, so never in p[]:
# the raw head, plus the anchoring mode and its group id.
OFF_BAND = ["originX", "originY", "originUnit", "space", "group"]


def layout(shader) -> list[str]:
    """The p[] the C++ sends: the resolved head, the rest alphabetically, the clock."""
    args = shader.jsonSerialization()
    numeric = sorted(k for k, v in args.items() if isinstance(v, (int, float)) and k not in OFF_BAND)
    return HEAD + numeric + ["elapsed"]


def documented(glsl: str) -> dict[int, str]:
    """The `// p[N] = name` slots the .glsl documents about itself."""
    with open(glsl) as f:
        return {int(m.group(1)): m.group(2) for m in re.finditer(r"// p\[(\d+)\]\s*= (\w+)", f.read())}


# ── C++ discrimination ──────────────────────────────────────────────────────
section("evilEye — serializes as a MathShader")
eye = evilEye()
ser = eye.jsonSerialization()

check("is a mathShader", isinstance(eye, mathShader))
check("the C++ factory name stays MathShader", ser["shader"] == "MathShader")
check("the glsl rides filepath (a string, so excluded from p[])", ser["filepath"] == EVIL_EYE_GLSL)

# ── p[] layout ──────────────────────────────────────────────────────────────
section("evilEye — the p[] layout matches what the glsl documents")
slots = layout(eye)
doc = documented(EVIL_EYE_GLSL)

check("the resolved origin + unit are p[0..2], before the alphabetical args", slots[0:3] == HEAD)
check("p[3..9] are color, fps, intensity, pupilSize, quality, scale, speed", slots[3:10] == ["color", "fps", "intensity", "pupilSize", "quality", "scale", "speed"])
check("neither the anchoring mode nor its group id shifts the args", all(k not in slots for k in ("space", "group")))
check("the frame clock is last", slots[-1] == "elapsed")
check("the glsl documents its slots at all", len(doc) > 0)
for i, name in sorted(doc.items()):
    if i < len(HEAD):   # the fixed head documents itself in prose
        continue
    check(f"the glsl reads {name} at p[{i}], and that is where it is sent", slots[i] == name)
# EffectPC holds 24 floats; anything past that is silently dropped.
check("the whole layout fits the 24 push-constant slots", len(slots) <= 24)

# ── origin ──────────────────────────────────────────────────────────────────
section("mathShader — origin defaults to the host's centre")
check("default origin is 50%/50% — half width, half height", (ser["originX"], ser["originY"]) == (50, 50))
check("percent is the default unit", ser["originUnit"] == 0.0)

pct = starNest(origin=(15, 85)).jsonSerialization()
check("a percent origin rides through", (pct["originX"], pct["originY"]) == (15, 85))
check("...still flagged as percent", pct["originUnit"] == 0.0)

px = starNest(origin=(300, 40), pixels=True).jsonSerialization()
check("a pixel origin rides through", (px["originX"], px["originY"]) == (300, 40))
check("...flagged as pixels", px["originUnit"] == 1.0)

check("every preset takes the origin", "originX" in starNest().jsonSerialization())

# ── packed colour ───────────────────────────────────────────────────────────
section("evilEye — colour packed into one float")
check("default #FF6F37 packs to 0xFF6F37", ser["color"] == float(0xFF6F37))
check("white packs to 0xFFFFFF", evilEye(color=rgba("#FFFFFF")).jsonSerialization()["color"] == float(0xFFFFFF))
check("black packs to 0", evilEye(color=rgba("#000000")).jsonSerialization()["color"] == 0.0)
# The unpacking in the glsl is exact only while the value stays under 2^24.
check("the packed value never leaves float32's exact-integer range", evilEye(color=rgba("#FFFFFF")).jsonSerialization()["color"] < 2**24)

# ── args ────────────────────────────────────────────────────────────────────
section("evilEye — args reach the serialization")
custom = evilEye(color=rgba("#7FD4FF"), intensity=2.0, pupilSize=1.1, scale=1.3, speed=0.5, quality=0.25).jsonSerialization()
check("intensity", custom["intensity"] == 2.0)
check("pupilSize", custom["pupilSize"] == 1.1)
check("scale", custom["scale"] == 1.3)
check("speed", custom["speed"] == 0.5)
check("quality", custom["quality"] == 0.25)
check("colour survives the round trip", custom["color"] == float(0x7FD4FF))

summary()
