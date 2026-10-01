#!/usr/bin/env python3
"""
A member built inside `Context.noRegister()` never reaches the stack, but what
is written on it still lands on its meta: `CompoundPolygon` reads the position
of each member to place its contours. Lost, every line of a `Plane` piled up on
the centre of the frame and drew one bright cross instead of a faint grid.
"""
import sys

sys.path.insert(0, ".")

from videocode import *  # noqa: E402
from videocode.template.input.Plane import Plane  # noqa: E402

with Context.noRegister():
    line = VerticalLine(length=5).position(x=3, y=1, offset=0)
assert (line.meta.position.x, line.meta.position.y) == (3, 1), line.meta.position

columns = {round(c[0][0], 2) for c in Plane().grid._all_contours}
assert len(columns) > 50, f"the grid's lines sit on {len(columns)} distinct x, not one per line"

print("All checks passed.")
