#!/usr/bin/env python3

from __future__ import annotations

from videocode.input.interface.Group import _GROUP_T, Group
from videocode.input.input import Input
from videocode.shader.vertexShader.position import position
from videocode.ty import *
from videocode.constants import *

__all__ = ["Row", "Column", "Grid"]

# Which way the cross-axis offset points: `START` is the top of a Row and the
# left of a Column, so a Row adds and a Column subtracts.
_SIDE = {Align.START: 1, Align.CENTER: 0, Align.END: -1}


def _place(inp: Input, x: wnumber, y: wnumber) -> None:
    # A group's `meta.position` is a displacement from its pivot, not a
    # location — see `_MemberBase.parentInverse` — so aim the content, not the
    # field. Zero for a leaf, whose anchor IS its position.
    pivot = Group._anchorOf(inp) - v2(inp.meta.position.x or 0, inp.meta.position.y or 0)
    inp.apply(position(x - pivot.x, y - pivot.y))


class Row(Group[_GROUP_T]):
    """
    Lay inputs out left to right, `gap` apart EDGE TO EDGE, centred on the
    group's position::

        Row(Rectangle(width=4, height=2), Circle(radius=1), gap=0.5)

    puts the circle's left edge 0.5 world units right of the rectangle's right
    edge — which `XAlign` cannot say: its `gap` is a centre-to-centre pitch
    that knows nothing of widths. Sizes and `gap` are world units (120 px; the
    1080p world is 16 x 9). The formation is centred whatever the count, even
    ones included.

    `align` places members across the line: `Align.START` flushes their tops,
    `Align.END` their bottoms, `Align.CENTER` (default) their middles.

    Laid out at construction, like `XAlign`, so the rigid-body snapshot is
    correct and position/scale/rotation applied to the row carry the
    formation. That is also the ceiling: a member that grows or is replaced
    later does not reflow the row — build a new one.
    """

    def __init__(self, *inputs: Input, gap: wnumber = 0.25, align: Align = Align.CENTER):
        widths = [i.width for i in inputs]
        tallest = max((i.height for i in inputs), default=0)
        x = -(sum(widths) + gap * (len(inputs) - 1)) / 2
        for inp, w in zip(inputs, widths):
            _place(inp, x + w / 2, _SIDE[align] * (tallest - inp.height) / 2)
            x += w + gap
        super().__init__(*inputs)


class Column(Group[_GROUP_T]):
    """
    `Row` turned top to bottom: `gap` is edge to edge in world units, the
    stack is centred on the group's position, and `align` flushes members'
    lefts (`Align.START`), rights (`Align.END`) or centres. Laid out once, at
    construction — see `Row` for what that means and what it cannot do.
    """

    def __init__(self, *inputs: Input, gap: wnumber = 0.25, align: Align = Align.CENTER):
        heights = [i.height for i in inputs]
        widest = max((i.width for i in inputs), default=0)
        y = (sum(heights) + gap * (len(inputs) - 1)) / 2
        for inp, h in zip(inputs, heights):
            _place(inp, -_SIDE[align] * (widest - inp.width) / 2, y - h / 2)
            y -= h + gap
        super().__init__(*inputs)


class Grid(Group[_GROUP_T]):
    """
    Inputs in reading order over `cols` columns, each column as wide as its
    widest member and each row as tall as its tallest, every cell centred on
    its member; a last row that does not fill up stays flush left. The whole
    is centred on the group's position. `gap` is edge to edge in world units,
    `rowGap`/`colGap` override it per axis. Laid out once, at construction —
    see `Row`.
    """

    def __init__(self, *inputs: Input, cols: int, gap: wnumber = 0.25, rowGap: maybe[wnumber] = None, colGap: maybe[wnumber] = None):
        if cols < 1:
            raise ValueError("Grid needs at least one column")
        rowGap = gap if rowGap is None else rowGap
        colGap = gap if colGap is None else colGap
        rows = -(-len(inputs) // cols)
        colWidths = [max((i.width for i in inputs[c::cols]), default=0) for c in range(cols)]
        rowHeights = [max(i.height for i in inputs[r * cols : (r + 1) * cols]) for r in range(rows)]

        xs: list[wnumber] = []
        x = -(sum(colWidths) + colGap * (cols - 1)) / 2
        for w in colWidths:
            xs.append(x + w / 2)
            x += w + colGap
        ys: list[wnumber] = []
        y = (sum(rowHeights) + rowGap * (rows - 1)) / 2
        for h in rowHeights:
            ys.append(y - h / 2)
            y -= h + rowGap

        for k, inp in enumerate(inputs):
            _place(inp, xs[k % cols], ys[k // cols])
        super().__init__(*inputs)
