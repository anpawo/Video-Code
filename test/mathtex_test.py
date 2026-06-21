#!/usr/bin/env python3

"""
Assertion-based smoke tests for `MathTex`/`Tex` (#39): LaTeX -> SVG -> vector
shapes via `_TexHelper.texToSVG` + `_SVGHelper.buildPaths`. Covers shape
generation, default/overridden fill color, recoloring propagation, the
`.cache/tex` compile cache, and `Tex`'s non-math mode.
Run directly: `python3 test/mathtex_test.py`
"""

import os
import sys

sys.path.insert(0, ".")
sys.path.insert(0, "test")
from helpers import check, section, summary

from videocode import MathTex, Tex, Context, WHITE, RED_A, BLUE_A
from videocode.input.shape.tex import _TexHelper

def pushedArg(index: int, key: str) -> bool:
    return any(key in entry for f, entry in Context.stack[index].items() if f != -1)

# ── MathTex: shape generation ────────────────────────────────────────────────
section("MathTex — compiles LaTeX to a group of non-empty SVGPath shapes")
formula = MathTex(r"\frac{1}{2} + \int_0^1 x^2 \, dx")

check("at least one shape was produced", len(formula.inputs) > 0)
check("every shape has non-empty points", all(len(o.points) > 0 for o in formula.inputs))

# ── Default / overridden fill color ──────────────────────────────────────────
section("MathTex — default fillColor is WHITE, override applies to every shape")
check("default fillColor is WHITE on every shape", all(o.fillColor == WHITE for o in formula.inputs))

red = MathTex(r"\frac{1}{2}", fillColor=RED_A)
check("fillColor override applies to every shape", all(o.fillColor == RED_A for o in red.inputs))

# ── Recoloring after construction propagates ────────────────────────────────
section("MathTex.fillColor = ... — recolors every shape and pushes Args:fillColor")
red.fillColor = BLUE_A
check("every shape recolored to BLUE_A", all(o.fillColor == BLUE_A for o in red.inputs))
check("Args:fillColor pushed on the stack", pushedArg(red.inputs[0].meta.index, "Args:fillColor"))

# ── Tex: non-math mode ────────────────────────────────────────────────────────
section("Tex — non-math mode also produces shapes")
text = Tex("Hello World")
check("Tex produces at least one shape", len(text.inputs) > 0)

# ── .cache/tex compile cache ─────────────────────────────────────────────────
section("_TexHelper.texToSVG — second call with the same source is cached")
svgPath1 = _TexHelper.texToSVG(r"\sqrt{2}")
mtime1 = os.path.getmtime(svgPath1)
svgPath2 = _TexHelper.texToSVG(r"\sqrt{2}")
mtime2 = os.path.getmtime(svgPath2)
check("same cached SVG path returned", svgPath1 == svgPath2)
check("cached SVG file was not regenerated", mtime1 == mtime2)

# ── summary ────────────────────────────────────────────────────────────────
summary()
