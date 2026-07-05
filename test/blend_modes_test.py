#!/usr/bin/env python3

"""
Assertion-based tests for per-input blend modes.
- string → pipeline-index resolution on the `blendMode` VertexShader
- `.blendMode(...)` lands a `BlendMode` entry in the stack with the resolved int
- autodestroy skips a no-op re-apply of the same mode
- invalid mode names are rejected
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
section("blendMode — string resolves to pipeline index")

check("normal -> 0", blendModeShader("normal").mode == 0)
check("multiply -> 1", blendModeShader("multiply").mode == 1)
check("screen -> 2", blendModeShader("screen").mode == 2)
check("add -> 3", blendModeShader("add").mode == 3)

rejected = False
try:
    blendModeShader("overlay")  # type: ignore[arg-type]
except ValueError:
    rejected = True
check("unknown mode rejected", rejected)

# ---------------------------------------------------------------------------
section("blendMode — lands in the stack as the resolved int")

r = Rectangle(width=1, height=1).blendMode("multiply")
bm = framesWith(r.meta.index, "BlendMode")
check("BlendMode entry present", len(bm) == 1)
entry = next(iter(bm.values()))
check("stack carries the int, not the string", entry["args"]["mode"] == 1)
check("shaderType is VertexShader", entry["type"] == "VertexShader")

# ---------------------------------------------------------------------------
section("blendMode — autodestroy skips a no-op re-apply")

r2 = Rectangle(width=1, height=1).blendMode("screen")
r2.blendMode("screen")  # same mode again — should autodestroy (single stack entry)
bm2 = framesWith(r2.meta.index, "BlendMode")
check("re-applying the same mode does not stack twice", len(bm2) == 1)

r2.blendMode("add")  # different mode — must register
check("meta reflects the latest mode", r2.meta.blendMode == 3)

# ---------------------------------------------------------------------------
summary()
