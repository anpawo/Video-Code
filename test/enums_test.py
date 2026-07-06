#!/usr/bin/env python3

"""
Assertion-based tests for the typed-enum API surface (`constants.py`):
`Direction`, `Axis`, `UVMapping`, plus `BlendMode` (blendMode.py).

These replaced stringly-typed params (`Literal["left", ...]` duplicated across
slide/wipe/transitions, `Literal["x","y","both"]` on shake, and the uvMapping
Literal on Image/Video). The serialization-sensitive ones have a contract:
- `BlendMode` is an IntEnum — must reach the JSON stack as a plain int
  (pipeline index, matches BlendModes.hpp).
- `UVMapping` is a StrEnum — must reach the stack as the plain lowercase
  string the C++ parser in BezierPath.cpp compares against.

Run directly: `python3 test/enums_test.py`
"""

import sys

sys.path.insert(0, ".")
sys.path.insert(0, "test")
from helpers import check, section, summary

from videocode import *

# ── Direction ────────────────────────────────────────────────────────────────
section("Direction — unit vectors in world coordinates (Y positive-up)")

check("LEFT vector", Direction.LEFT.vector == (-1.0, 0.0))
check("RIGHT vector", Direction.RIGHT.vector == (1.0, 0.0))
check("TOP vector (world Y up)", Direction.TOP.vector == (0.0, 1.0))
check("BOTTOM vector", Direction.BOTTOM.vector == (0.0, -1.0))

section("Direction — opposite is an involution")

check("LEFT <-> RIGHT", Direction.LEFT.opposite is Direction.RIGHT and Direction.RIGHT.opposite is Direction.LEFT)
check("TOP <-> BOTTOM", Direction.TOP.opposite is Direction.BOTTOM and Direction.BOTTOM.opposite is Direction.TOP)
check("double opposite is identity", all(d.opposite.opposite is d for d in Direction))

section("Direction — .side matches crop()'s kwarg names")

check("side names", [d.side for d in Direction] == ["left", "right", "top", "bottom"])

# ── Axis ─────────────────────────────────────────────────────────────────────
section("Axis — members")

check("three members", set(Axis) == {Axis.X, Axis.Y, Axis.BOTH})

# ── UVMapping — StrEnum serialization contract with BezierPath.cpp ──────────
section("UVMapping — members ARE the plain strings the C++ parser expects")

check("stretch", UVMapping.STRETCH == "stretch")
check("radial", UVMapping.RADIAL == "radial")
check("conic", UVMapping.CONIC == "conic")
check("is a str subclass (pyToJson takes the py::str branch)", all(isinstance(m, str) for m in UVMapping))

# ── BlendMode — IntEnum serialization contract with BlendModes.hpp ──────────
section("BlendMode — values ARE the C++ pipeline indices")

check("pipeline indices 0..3", [m.value for m in BlendMode] == [0, 1, 2, 3])
check("is an int subclass (pyToJson takes the py::int_ branch)", all(isinstance(m, int) for m in BlendMode))
check("NORMAL is the Metadata default", BlendMode.NORMAL == 0 and Metadata().blendMode == 0)

# ── summary ──────────────────────────────────────────────────────────────────
summary()
