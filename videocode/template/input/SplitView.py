#!/usr/bin/env python3

from __future__ import annotations

from videocode.input.shape.Rectangle import Rectangle
from videocode.input.interface.Group import Group
from videocode.ty import *
from videocode.constants import *

__all__ = ["SplitView", "Panel"]


class Panel(Group):
    def __init__(
        self,
        width: wnumber,
        height: wnumber,
        x: wnumber = 0,
        y: wnumber = 0,
        padding: wnumber = 0.3,
        fillColor: rgba = BLACK | 0.5,
        strokeColor: rgba = WHITE,
        strokeWidth: wnumber = 0.025,
        cornerRadius: percent = 10,
    ):
        self.w = width
        self.h = height
        self.x = x
        self.y = y
        self.padding = padding

        self.rect = Rectangle(
            width=width,
            height=height,
            fillColor=fillColor,
            strokeColor=strokeColor,
            strokeWidth=strokeWidth,
            cornerRadius=cornerRadius,
        ).position(x, y)

        super().__init__(self.rect)

    @property
    def width(self) -> wnumber:
        return self.w

    @property
    def height(self) -> wnumber:
        return self.h

    @property
    def left(self) -> wnumber:
        return self.x - self.w / 2 + self.padding

    @property
    def right(self) -> wnumber:
        return self.x + self.w / 2 - self.padding

    @property
    def top(self) -> wnumber:
        return self.y + self.h / 2 - self.padding

    @property
    def bot(self) -> wnumber:
        return self.y - self.h / 2 + self.padding

    @property
    def cx(self) -> wnumber:
        return self.x

    @property
    def cy(self) -> wnumber:
        return self.y

    @property
    def innerWidth(self) -> wnumber:
        return self.w - 2 * self.padding

    @property
    def innerHeight(self) -> wnumber:
        return self.h - 2 * self.padding


class SplitView(Group):
    """
    Two panels dividing the frame, `a` then `b`, with `ratio` sizing the
    second against the first.

    `split` chooses the axis — and defaults to following the frame, so the
    same scene stays readable at any resolution: side by side at
    16x9, stacked at 1:1 or 9x16, where two columns would each be too narrow
    to hold anything. `a`/`b` and every `Panel` property
    (`left`/`top`/`cx`/`innerWidth`/...) mean the same thing in both, so a
    scene written against them needs no changes.

        sv = SplitView(ratio=3 / 5)                    # columns at 16x9, rows at 9x16
        sv = SplitView(ratio=3 / 5, split=Split.ROWS)  # stacked, whatever the frame

    Named like CSS grid — `COLUMNS` = two columns (a | b), `ROWS` = two rows
    (a over b). See `Split`. Note that in a 16x9 world `AUTO` already resolves
    to `COLUMNS`, so passing it explicitly changes nothing there; the two
    differ only once the frame is square or portrait (`--width`/`--height`).

    - `ratio`: `b`'s extent as a fraction of `a`'s, along the split axis
      (width in `COLUMNS`, height in `ROWS`).
    - `marginX`/`marginY`: the gutters. The split axis gets three of them
      (outer, between, outer), the cross axis two.
    - `panelHeight`: forces the panel height in `COLUMNS`. Ignored in `ROWS`,
      where the heights are what the split itself decides.
    """

    def __init__(
        self,
        # `None`, not `W / 48`: a default argument is evaluated once, at import
        # time, so a literal here would freeze the gutters at whatever the world
        # was THEN — and `setScreen` cannot reach a default (it says so). That
        # is invisible on the normal path but wrong in the one place the size
        # changes mid-process: the visual suite, which renders portrait cases
        # after landscape ones. Resolved below against the live world box.
        marginX: wnumber | None = None,
        marginY: wnumber | None = None,
        panelHeight: wnumber | None = None,
        padding: wnumber = 0.3,
        fillColor: rgba = BLACK | 0.5,
        strokeColor: rgba = WHITE,
        strokeWidth: wnumber = 0.025,
        cornerRadius: percent = 10,
        ratio: float = 2 / 3,  # second panel's extent as a fraction of the first's
        split: Split = Split.AUTO,
    ):
        # AUTO reads the world box, which already tracks the output
        # resolution (--width/--height). A landscape frame splits into
        # columns, anything square or taller into rows.
        self.split = Split.COLUMNS if (split == Split.AUTO and W > H) else Split.ROWS if split == Split.AUTO else split

        # Gutters as a fraction of the world, read now rather than at import.
        if marginX is None:
            marginX = W / 48
        if marginY is None:
            marginY = W / 24

        if self.split == Split.COLUMNS:
            total: wnumber = W - 3 * marginX
            pWa: wnumber = total / (1 + ratio)
            pWb: wnumber = total - pWa
            pHa = pHb = panelHeight if panelHeight is not None else H - 2 * marginY
            xA: wnumber = -W / 2 + marginX + pWa / 2
            xB: wnumber = -W / 2 + 2 * marginX + pWa + pWb / 2
            yA = yB = 0.0
        else:
            # Transposed: the split axis is Y, and `a` sits on TOP so a/b
            # still read in the order they are written.
            total = H - 3 * marginY
            pHa = total / (1 + ratio)
            pHb = total - pHa
            pWa = pWb = W - 2 * marginX
            yA = H / 2 - marginY - pHa / 2
            yB = H / 2 - 2 * marginY - pHa - pHb / 2
            xA = xB = 0.0

        self.a = Panel(
            width=pWa,
            height=pHa,
            x=xA,
            y=yA,
            padding=padding,
            fillColor=fillColor,
            strokeColor=strokeColor,
            strokeWidth=strokeWidth,
            cornerRadius=cornerRadius,
        )
        self.b = Panel(
            width=pWb,
            height=pHb,
            x=xB,
            y=yB,
            padding=padding,
            fillColor=fillColor,
            strokeColor=strokeColor,
            strokeWidth=strokeWidth,
            cornerRadius=cornerRadius,
        )

        super().__init__(self.a, self.b)
