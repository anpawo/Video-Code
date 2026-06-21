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
        strokeInside: bool = True,
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
            strokeInside=strokeInside,
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
    def __init__(
        self,
        marginX: wnumber = W / 48,
        marginY: wnumber = W / 24,
        panelHeight: wnumber | None = None,
        padding: wnumber = 0.3,
        fillColor: rgba = BLACK | 0.5,
        strokeColor: rgba = WHITE,
        strokeWidth: wnumber = 0.025,
        cornerRadius: percent = 10,
        strokeInside: bool = True,
    ):
        pW: wnumber = (W - 3 * marginX) / 2
        pH: wnumber = panelHeight if panelHeight is not None else H - 2 * marginY
        pX: wnumber = W / 2 - marginX - pW / 2

        self.a = Panel(
            width=pW,
            height=pH,
            x=-pX,
            y=0,
            padding=padding,
            fillColor=fillColor,
            strokeColor=strokeColor,
            strokeWidth=strokeWidth,
            cornerRadius=cornerRadius,
            strokeInside=strokeInside,
        )
        self.b = Panel(
            width=pW,
            height=pH,
            x=pX,
            y=0,
            padding=padding,
            fillColor=fillColor,
            strokeColor=strokeColor,
            strokeWidth=strokeWidth,
            cornerRadius=cornerRadius,
            strokeInside=strokeInside,
        )

        super().__init__(self.a, self.b)
