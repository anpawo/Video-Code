#!/usr/bin/env python3

"""
Assertion-based tests for track mattes / masks (Tier 2).
- `.matte(source)` lands a `Matte` VertexShader entry in Context.stack whose
  `args.source` equals the source input's meta.index
- applying it sets meta.matteSource
- autodestroy skips a no-op re-apply of the same source
Run directly: `python3 test/matte_test.py`
"""

import sys

sys.path.insert(0, ".")
sys.path.insert(0, "test")
from helpers import check, section, summary

from videocode import *
from videocode.template.input.CompoundPolygon import CompoundPolygon


def framesWith(index: int, key: str) -> dict[int, dict]:
    return {f: entry[key] for f, entry in Context.stack[index].items() if f != -1 and key in entry}


# ---------------------------------------------------------------------------
section("matte — lands in the stack referencing the source index")

# The matte source is a single Input (has a meta.index). A multi-letter Text is
# a Group of Letters (no single index), so the flagship silhouette is merged
# into one input via CompoundPolygon — see the visual scene.
with Context.noRegister():
    letters = Text("MASK", fontSize=1).inputs
src = CompoundPolygon(*letters)
content = Rectangle(width=4, height=2).matte(src)

m = framesWith(content.meta.index, "Matte")
check("Matte entry present", len(m) == 1)
entry = next(iter(m.values()))
check("shaderType is VertexShader", entry["type"] == "VertexShader")
check("args.source == source meta.index", entry["args"]["source"] == src.meta.index)
check("meta.matteSource reflects the source", content.meta.matteSource == src.meta.index)

# ---------------------------------------------------------------------------
section("matte — source is a plain int, not the Input object")

check("stored source is an int", isinstance(entry["args"]["source"], int))

# ---------------------------------------------------------------------------
section("matte — autodestroy skips a no-op re-apply of the same source")

src2 = Circle(radius=1)
c2 = Rectangle(width=2, height=2).matte(src2)
c2.matte(src2)  # same source again — should autodestroy (single stack entry)
m2 = framesWith(c2.meta.index, "Matte")
check("re-applying the same source does not stack twice", len(m2) == 1)

# ---------------------------------------------------------------------------
summary()
