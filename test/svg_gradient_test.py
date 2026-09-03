#!/usr/bin/env python3

"""
Assertion-based tests for gradient paints in SVG files — `fill="url(#g)"` and
`stroke="url(#g)"`, the way every icon exporter writes them. Covers stop
colors/offsets/opacity, the y-down → y-up angle flip, radial gradients, the
BLACK + warning fallback for what this parser refuses, and that solid fills and
explicit overrides are untouched. No renderer, no latex.
Run directly: `python3 test/svg_gradient_test.py`
"""

import io
import os
import sys
import tempfile

sys.path.insert(0, ".")
sys.path.insert(0, "test")
from helpers import check, section, summary

from videocode import SVG, WHITE, BLACK
from videocode.ty import LinearGradient, RadialGradient, rgba
import videocode.input.shape.svg._SVGHelper as svgHelper
from videocode.input.shape.svg._SVGHelper import buildPaths, parseSVG, _parseGradients

_tmp = tempfile.TemporaryDirectory()


def writeSVG(name: str, body: str) -> str:
    path = os.path.join(_tmp.name, name)
    with open(path, "w") as f:
        f.write(f'<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100">{body}</svg>')
    return path


def linear(gid: str, coords: str = 'x1="0" y1="0" x2="1" y2="0"') -> str:
    return f"""<linearGradient id="{gid}" {coords}>
        <stop offset="0" stop-color="#ff0000"/>
        <stop offset="1" stop-color="#0000ff" stop-opacity="0.5"/>
      </linearGradient>"""


def captureWarnings() -> io.StringIO:
    """`_WARN` bound the real stderr at import, so `redirect_stderr` cannot see it."""
    sink = io.StringIO()
    svgHelper._WARN.file = sink
    return sink


BASIC = writeSVG(
    "basic.svg",
    f'<defs>{linear("g")}</defs><rect x="5" y="5" width="30" height="30" fill="url(#g)"/>',
)

# ── the paint that used to be silently black ─────────────────────────────────
section("fill=url(#g) — a gradient, not BLACK")
fill = SVG(BASIC).inputs[0].fillColor
check("fillColor is a LinearGradient", isinstance(fill, LinearGradient))
check("and is no longer BLACK", fill != BLACK)

# ── stops ────────────────────────────────────────────────────────────────────
section("stops — color, offset, opacity")
stops = fill.stops
check("two stops", len(stops) == 2)
check("offset 0 → 0%, opaque red", stops[0] == (rgba(255, 0, 0, 255), 0.0))
check("offset 1 → 100%, blue at stop-opacity 0.5", stops[1] == (rgba(0, 0, 255, 128), 100.0))

pct = writeSVG(
    "percent.svg",
    """<defs><linearGradient id="g">
         <stop offset="0%" stop-color="#ff0000"/>
         <stop offset="50%" style="stop-color:#00ff00;stop-opacity:0.5"/>
         <stop offset="100%" stop-color="#0000ff"/>
       </linearGradient></defs><rect width="30" height="30" fill="url(#g)"/>""",
)
mid = SVG(pct).inputs[0].fillColor.stops
check("offset written as 50% lands at 50.0", mid[1][1] == 50.0)
check("style='stop-color:...' read like the attribute", mid[1][0] == rgba(0, 255, 0, 128))

# ── angle: SVG's y points down, the engine's 90 is bottom → top ──────────────
section("angle — the y flip")


def angleOf(coords: str) -> float:
    path = writeSVG(f"a{abs(hash(coords))}.svg", f'<defs>{linear("g", coords)}</defs><rect width="9" height="9" fill="url(#g)"/>')
    return SVG(path).inputs[0].fillColor.angle


check("left → right is 0", angleOf('x1="0" y1="0" x2="1" y2="0"') == 0)
check("bottom → top (y1=1, y2=0) is 90", angleOf('x1="0" y1="1" x2="0" y2="0"') == 90)
check("(0,0) → (1,1) is -45", angleOf('x1="0" y1="0" x2="1" y2="1"') == -45)
check("x1/x2 default to 0/1 → 0", angleOf('') == 0)

# ── radial, and stroke ───────────────────────────────────────────────────────
section("radialGradient and stroke=url(#g)")
both = writeSVG(
    "both.svg",
    f"""<defs>{linear("g")}
      <radialGradient id="r">
        <stop offset="0" stop-color="#ff0000"/>
        <stop offset="1" stop-color="#0000ff" stop-opacity="0.5"/>
      </radialGradient></defs>
    <circle cx="50" cy="50" r="20" fill="url(#r)" stroke="url(#g)" stroke-width="3"/>""",
)
circle = SVG(both).inputs[0]
check("fill=url(#r) is a RadialGradient", isinstance(circle.fillColor, RadialGradient))
check("radial keeps the same stops", circle.fillColor.stops == [(rgba(255, 0, 0, 255), 0.0), (rgba(0, 0, 255, 128), 100.0)])
check("stroke=url(#g) is a LinearGradient", isinstance(circle.strokeColor, LinearGradient))
check("stroke gradient keeps its stops", circle.strokeColor.stops == fill.stops)

# ── what this parser refuses must SAY so ─────────────────────────────────────
section("unresolvable paints — BLACK, and a warning that is actually emitted")
refused = writeSVG(
    "refused.svg",
    """<defs><pattern id="pat" width="4" height="4"><rect width="2" height="2" fill="#000"/></pattern>
       <linearGradient id="xf" gradientTransform="rotate(45)">
         <stop offset="0" stop-color="#ff0000"/><stop offset="1" stop-color="#0000ff"/>
       </linearGradient>
       <linearGradient id="usr" gradientUnits="userSpaceOnUse" x1="0" x2="100">
         <stop offset="0" stop-color="#ff0000"/><stop offset="1" stop-color="#0000ff"/>
       </linearGradient>
       <linearGradient id="inherit" href="#xf"/></defs>
    <rect y="0" width="9" height="9" fill="url(#missing)"/>
    <rect y="10" width="9" height="9" fill="url(#pat)"/>
    <rect y="20" width="9" height="9" fill="url(#xf)"/>
    <rect y="30" width="9" height="9" fill="url(#usr)"/>
    <rect y="40" width="9" height="9" fill="url(#inherit)"/>""",
)
warnings = captureWarnings()
fills = [p.fillColor for p in SVG(refused).inputs]
text = warnings.getvalue()
for i, what in enumerate(["missing", "pat", "xf", "usr", "inherit"]):
    check(f"url(#{what}) falls back to BLACK", fills[i] == BLACK)
    check(f"url(#{what}) warns", f"url(#{what})" in text)
check("no gradient registered for a pattern id", "pat" not in _parseGradients(refused))

# ── nothing solid changes ────────────────────────────────────────────────────
section("solid fills and explicit overrides are untouched")
check("buildPaths(fillColor=WHITE) still overrides", all(p.fillColor == WHITE for p in buildPaths(BASIC, None, None, fillColor=WHITE)))
icon = [(f, s) for _, f, s, _ in parseSVG("icon.svg", None, None)]
check("icon.svg rect stays #FC6255", icon[0][0] == rgba("#FC6255"))
check("icon.svg circle stays unfilled, stroked #58C4DD", icon[1][0].a == 0 and icon[1][1] == rgba("#58C4DD"))
check("icon.svg path stays #9ADF8E", icon[2][0] == rgba("#9ADF8E"))
check("a solid file registers no gradients", _parseGradients("icon.svg") == {})

summary()
