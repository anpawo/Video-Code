#!/usr/bin/env python3

"""
Assertion-based tests for LUT color grading (Tier 2).

Two halves:
  1. `.apply(lut(...))` lands a `Lut` FragmentShader entry in Context.stack,
     carrying the .cube `filepath` (a STRING — read directly off the args dict
     C++-side, NOT via the numeric push-constant path) and `intensity`.
  2. The .cube fixtures under assets/luts/ are well-formed: right LUT_3D_SIZE and
     the exact sample values the C++ parser (LutAtlas.hpp) must reproduce at
     known corners. The C++ parser itself is exercised end-to-end by the visual
     regression scene (test/visual/scenes/lut.py).
Run directly: `python3 test/lut_test.py`
"""

import sys

sys.path.insert(0, ".")
sys.path.insert(0, "test")
from helpers import check, section, summary

from videocode import *

IDENTITY = "assets/luts/identity16.cube"
WARM = "assets/luts/warm.cube"


def framesWith(index: int, key: str) -> dict[int, dict]:
    return {f: entry[key] for f, entry in Context.stack[index].items() if f != -1 and key in entry}


def parseCube(path: str):
    """Tiny reference parser — documents the contract LutAtlas.hpp must honor."""
    size = 0
    samples = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            tok = line.split()
            if tok[0] == "LUT_3D_SIZE":
                size = int(tok[1])
                continue
            if tok[0] in ("TITLE", "DOMAIN_MIN", "DOMAIN_MAX"):
                continue
            try:
                r, g, b = float(tok[0]), float(tok[1]), float(tok[2])
            except (ValueError, IndexError):
                continue
            samples.append((r, g, b))
    return size, samples


# ---------------------------------------------------------------------------
section("lut — binding and stack presence")

l = lut(WARM, intensity=0.8)
check("filepath/intensity stored", l.filepath == WARM and l.intensity == 0.8)

r = Rectangle(width=1, height=1)
r.apply(lut(WARM, intensity=0.5), duration=0.3)
luts = framesWith(r.meta.index, "Lut")
check("Lut lands in the stack", len(luts) > 0)

entry = next(iter(luts.values()))
check("shaderType is FragmentShader", entry["type"] == "FragmentShader")
check("filepath travels through the stack as a string",
      entry["args"]["filepath"] == WARM and isinstance(entry["args"]["filepath"], str))
check("intensity travels through the stack", entry["args"]["intensity"] == 0.5)

# ---------------------------------------------------------------------------
section("lut — intensity defaults to 1.0 (full grade)")

check("default intensity is 1.0", lut(IDENTITY).intensity == 1.0)

# ---------------------------------------------------------------------------
section("identity16.cube — 16^3 identity, exact corner values")

size, samples = parseCube(IDENTITY)
check("LUT_3D_SIZE is 16", size == 16)
check("sample count is 16^3", len(samples) == 16**3)

N = 16
# .cube order: R fastest, then G, then B. index(r,g,b) = r + g*N + b*N*N.
def idx(r, g, b):
    return r + g * N + b * N * N

check("identity black corner (0,0,0) -> (0,0,0)", samples[idx(0, 0, 0)] == (0.0, 0.0, 0.0))
check("identity white corner (15,15,15) -> (1,1,1)", samples[idx(15, 15, 15)] == (1.0, 1.0, 1.0))
# Pure-red corner: R=1, G=0, B=0 stays pure red under identity.
red = samples[idx(15, 0, 0)]
check("identity red corner (15,0,0) -> (1,0,0)", red == (1.0, 0.0, 0.0))

# ---------------------------------------------------------------------------
section("warm.cube — warm grade bends midtones, keeps corners")

wsize, wsamples = parseCube(WARM)
check("warm LUT_3D_SIZE is 16", wsize == 16)
# Corners preserved (black->black, white->white) by the per-channel gamma grade.
check("warm black corner unchanged", wsamples[idx(0, 0, 0)] == (0.0, 0.0, 0.0))
check("warm white corner unchanged", wsamples[idx(15, 15, 15)] == (1.0, 1.0, 1.0))
# Midtone gray (8/15 ~= 0.533): red lifted (gamma 0.6), blue crushed (gamma 1.6),
# so out.r > in > out.b — the warm shift, asserted directionally.
mid = wsamples[idx(8, 8, 8)]
inMid = 8 / 15
check("warm midtone lifts red above input", mid[0] > inMid)
check("warm midtone crushes blue below input", mid[2] < inMid)
check("warm midtone is warmer than neutral (r > b)", mid[0] > mid[2])

# ---------------------------------------------------------------------------
summary()
