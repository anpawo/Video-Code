#!/usr/bin/env python3

"""
Assertion-based tests for `Row`, `Column` and `Grid` (D2): the gap is measured
edge to edge, the formation is centred whatever the count, `align` picks the
cross-axis edge, and a Row inside a Column lands where the arithmetic says.
Every expected number below is worked out by hand in the comment beside it.
Run directly: `python3 test/layout_test.py`
"""

import sys

sys.path.insert(0, ".")
sys.path.insert(0, "test")
from helpers import check, section, summary

from videocode import Align, Rectangle, Square, Circle, Group
from videocode.template.input.Layout import Row, Column, Grid
from videocode.template.input.XAlign import XAlign


def approx(a: float, b: float, eps: float = 1e-6) -> bool:
    return abs(a - b) <= eps


def at(inp, x: float, y: float) -> bool:
    return approx(inp.meta.position.x, x) and approx(inp.meta.position.y, y)


# ── Row: the gap is edge to edge, not centre to centre ──────────────────────
# widths 4 and 2, gap 0.5: total 6.5, left edge at -3.25.
# rect centre  = -3.25 + 2           = -1.25   (right edge 0.75)
# circle centre = -3.25 + 4 + 0.5 + 1 = 2.25   (left edge 1.25)  → 0.5 apart
section("Row — gap is edge to edge for members of different widths")
rect = Rectangle(width=4, height=2)
circle = Circle(radius=1)
row = Row(rect, circle, gap=0.5)

check("rectangle centred at -1.25", at(rect, -1.25, 0))
check("circle centred at 2.25", at(circle, 2.25, 0))
check("right edge of rect to left edge of circle is 0.5", approx((circle.meta.position.x - 1) - (rect.meta.position.x + 2), 0.5))
check("the row spans 6.5", approx(row.width, 6.5))
check("the row is centred on the origin", approx((rect.meta.position.x - 2 + circle.meta.position.x + 1) / 2, 0))

row.position(5, 2)
check("moving the row carries the formation", at(rect, 3.75, 2) and at(circle, 7.25, 2))

# ── An even count is centred ────────────────────────────────────────────────
# Two unit squares, gap 1: total 3, centres at -1 and +1.
# XAlign(1, a, b) puts member i at (i - n//2) * gap = -1 and 0 — its centre
# is -0.5, which is the off-by-half its own comment admits for even counts.
section("Row — an even number of members is centred (XAlign is not)")
a, b = Square(1), Square(1)
Row(a, b, gap=1)
check("two members sit at -1 and +1", at(a, -1, 0) and at(b, 1, 0))

xa, xb = Square(1), Square(1)
XAlign(1, xa, xb)
check("(for contrast: XAlign's pair is centred on -0.5)", approx((xa.meta.position.x + xb.meta.position.x) / 2, -0.5))

# ── Row: align on the cross axis ────────────────────────────────────────────
# heights 4 and 2: the short one moves by (4 - 2) / 2 = 1 to meet an edge.
section("Row — align start / center / end")
for alignment, y in ((Align.START, 1), (Align.CENTER, 0), (Align.END, -1)):
    tall, short = Rectangle(width=1, height=4), Rectangle(width=1, height=2)
    Row(tall, short, gap=0, align=alignment)
    check(f"align={alignment!r}: tall stays at y=0, short at y={y}", at(tall, -0.5, 0) and at(short, 0.5, y))

# ── Column ──────────────────────────────────────────────────────────────────
# heights 1 and 3, gap 0.5: total 4.5, top edge at 2.25.
# first centre  = 2.25 - 0.5             = 1.75   (bottom edge 1.25)
# second centre = 2.25 - 1 - 0.5 - 1.5   = -0.75  (top edge 0.75)  → 0.5 apart
section("Column — gap is edge to edge on the vertical axis")
top, bottom = Rectangle(width=2, height=1), Rectangle(width=1, height=3)
col = Column(top, bottom, gap=0.5)
check("first centred at y=1.75", at(top, 0, 1.75))
check("second centred at y=-0.75", at(bottom, 0, -0.75))
check("the column spans 4.5", approx(col.height, 4.5))

# widths 2 and 1: the narrow one moves by (2 - 1) / 2 = 0.5 to meet an edge —
# left for START, right for END.
for alignment, x in ((Align.START, -0.5), (Align.CENTER, 0), (Align.END, 0.5)):
    wide, narrow = Rectangle(width=2, height=1), Rectangle(width=1, height=1)
    Column(wide, narrow, gap=0, align=alignment)
    check(f"align={alignment!r}: narrow at x={x}", at(wide, 0, 0.5) and at(narrow, x, -0.5))

# ── Grid ────────────────────────────────────────────────────────────────────
# Five members over two columns: three rows, the last one half full.
# Column widths [2, 1], row heights [1, 2, 1], gap 0.5.
# width  = 3 + 0.5 = 3.5 → left -1.75 → column centres -0.75 and 1.25
# height = 4 + 1   = 5   → top   2.5  → row centres 2, 0, -2
section("Grid — a row count that does not divide evenly")
cells = [
    Rectangle(width=2, height=1),
    Rectangle(width=1, height=1),
    Rectangle(width=1, height=2),
    Rectangle(width=1, height=1),
    Rectangle(width=1, height=1),
]
grid = Grid(*cells, cols=2, gap=0.5)
check("row 0", at(cells[0], -0.75, 2) and at(cells[1], 1.25, 2))
check("row 1", at(cells[2], -0.75, 0) and at(cells[3], 1.25, 0))
check("the odd one out stays in the first column", at(cells[4], -0.75, -2))
check("columns are 0.5 apart edge to edge", approx((cells[1].meta.position.x - 0.5) - (cells[0].meta.position.x + 1), 0.5))
check("rows are 0.5 apart edge to edge", approx((cells[0].meta.position.y - 0.5) - (cells[2].meta.position.y + 1), 0.5))
check("the grid spans 3.5 x 5", approx(grid.width, 3.5) and approx(grid.height, 5))

# Four unit squares, rowGap 1 and colGap 0: columns touch, rows are 1 apart.
sq = [Square(1) for _ in range(4)]
Grid(*sq, cols=2, rowGap=1, colGap=0)
check("rowGap/colGap override gap per axis", at(sq[0], -0.5, 1) and at(sq[1], 0.5, 1) and at(sq[2], -0.5, -1) and at(sq[3], 0.5, -1))

# ── Nesting: a Row inside a Column ──────────────────────────────────────────
# The row is 3 wide and 1 tall (squares at -1 and +1); with a 1x1 rectangle
# under it at gap 0.5 the column is 2.5 tall, top edge 1.25:
# row centre  = 1.25 - 0.5              = 0.75
# rect centre = 1.25 - 1 - 0.5 - 0.5    = -0.75
# `Group._anchorOf` must read the row's CONTENT, not its meta.position, for
# the squares to land at y=0.75 — a group's position is a displacement.
section("Column(Row(...), ...) — a nested row lands where the arithmetic says")
s1, s2 = Square(1), Square(1)
inner = Row(s1, s2, gap=1)
under = Rectangle(width=1, height=1)
outer = Column(inner, under, gap=0.5)
check("the row's squares moved up to y=0.75, still 2 apart", at(s1, -1, 0.75) and at(s2, 1, 0.75))
check("the rectangle sits at y=-0.75", at(under, 0, -0.75))
check("the column measures the row's real width", approx(outer.width, 3) and approx(outer.height, 2.5))

# A member group whose content is NOT at the origin: squares at x=3 and x=5
# form a group 3 wide centred on 4. In a row with a unit square at gap 0.5
# (total 4.5, left edge -2.25) that content must be centred at -0.75 — so the
# group is told to move by -4.75, not to -0.75. Placing its meta.position at
# -0.75 would leave the squares at 2.25 and 4.25.
section("Row(Group(...), ...) — a member group is placed by its content, not its position")
g1, g2 = Square(1).position(x=3), Square(1).position(x=5)
sq = Square(1)
Row(Group(g1, g2), sq, gap=0.5)
check("the group's squares land at -1.75 and 0.25", at(g1, -1.75, 0) and at(g2, 0.25, 0))
check("the square follows at 1.75", at(sq, 1.75, 0))

# ── summary ─────────────────────────────────────────────────────────────────
summary()
