#!/usr/bin/env python3

"""
Assertion-based tests for per-input blend modes.
- `BlendMode` is an `IntEnum` matching the C++ pipeline index
- `.blendMode(...)` lands a `BlendMode` entry in the stack with a plain int
- autodestroy skips a no-op re-apply of the same mode
Run directly: `python3 test/blend_modes_test.py`
"""

import sys

sys.path.insert(0, ".")
sys.path.insert(0, "test")
from helpers import check, section, summary

from videocode import *
from videocode.shader.vertexShader.blendMode import blendMode as blendModeShader


def framesWith(index: int, key: str) -> dict[int, dict]:
    return {f: entry[key] for f, entry in Context.stack[index].items() if f != -1 and key in entry}


# ---------------------------------------------------------------------------
section("BlendMode — IntEnum matches the C++ pipeline index")

check("NORMAL -> 0", blendModeShader(BlendMode.NORMAL).mode == 0)
check("MULTIPLY -> 1", blendModeShader(BlendMode.MULTIPLY).mode == 1)
check("SCREEN -> 2", blendModeShader(BlendMode.SCREEN).mode == 2)
check("ADD -> 3", blendModeShader(BlendMode.ADD).mode == 3)

# ---------------------------------------------------------------------------
section("blendMode — lands in the stack as a plain int")

r = Rectangle(width=1, height=1).blendMode(BlendMode.MULTIPLY)
bm = framesWith(r.meta.index, "BlendMode")
check("BlendMode entry present", len(bm) == 1)
entry = next(iter(bm.values()))
check("stack carries the resolved mode as int 1", entry["args"]["mode"] == 1)
check("shaderType is VertexShader", entry["type"] == "VertexShader")

# ---------------------------------------------------------------------------
section("blendMode — autodestroy skips a no-op re-apply")

r2 = Rectangle(width=1, height=1).blendMode(BlendMode.SCREEN)
r2.blendMode(BlendMode.SCREEN)  # same mode again — should autodestroy (single stack entry)
bm2 = framesWith(r2.meta.index, "BlendMode")
check("re-applying the same mode does not stack twice", len(bm2) == 1)

r2.blendMode(BlendMode.ADD)  # different mode — must register
check("meta reflects the latest mode", r2.meta.blendMode == 3)

# ---------------------------------------------------------------------------
summary()
