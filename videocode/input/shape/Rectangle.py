#!/usr/bin/env python3

from __future__ import annotations

from videocode.input.shape.Polygon import *
from videocode.utils.funcutils import size
from videocode.utils.logger import *


class Rectangle(Polygon):
    def __init__(
        self,
        width: wunumber = 3,
        height: wunumber = 2,
        fillColor: paint = BLUE_C | BLACK,
        strokeColor: rgba = BLUE_C | WHITE,
        strokeWidth: wunumber = 0.05,
        cornerRadius: percent = 0,  # percent 0-100, 100 = circle on a square
    ):
        # Square and HorizontalLine route through here, so this is the one
        # place a negative side has to be caught.
        self._width = size(type(self).__name__, "width", width)
        self._height = size(type(self).__name__, "height", height)

        super().__init__(
            vertices=self.generateVertices(),
            fillColor=fillColor,
            strokeColor=strokeColor,
            strokeWidth=strokeWidth,
            cornerRadius=cornerRadius,
        )

    def generateVertices(self) -> list[point]:
        return [
            (0, 0),
            (self._width, 0),
            (self._width, self._height),
            (0, self._height),
        ]

    @property
    def width(self) -> wunumber:
        """
        How wide the rectangle is DRAWN — its geometry times `meta.scale`, the
        same answer `Polygon.width` gives.

        Writing it sizes the geometry and leaves the transform alone, so
        `ease(r.ref.width, …)` on a scaled shape runs between two drawn sizes
        rather than reading one space and writing the other::

            r = Rectangle(width=3, height=1).scale(2)
            r.width          # 6 — what is on screen
            r.width = 8      # still scaled 2, geometry 4, drawn 8
        """
        return self._width * abs(self.meta.scale.x)

    @width.setter
    def width(self, value: wunumber) -> None:
        self._width = value / (abs(self.meta.scale.x) or 1)
        self.updatePoints()

    @property
    def height(self) -> wunumber:
        """How tall the rectangle is DRAWN. `width`'s reasoning, other axis."""
        return self._height * abs(self.meta.scale.y)

    @height.setter
    def height(self, value: wunumber) -> None:
        self._height = value / (abs(self.meta.scale.y) or 1)
        self.updatePoints()


class Square(Rectangle):
    def __init__(
        self,
        side: wunumber = 2,
        strokeWidth: wunumber = 0.05,
        fillColor: paint = GREEN_A | BLACK,
        strokeColor: rgba = GREEN_A | WHITE,
        cornerRadius: percent = 0,
    ):
        # Checked here rather than left to Rectangle: the author wrote `side`,
        # and being told about a `width` they never typed sends them looking
        # for a line they did not write.
        side = size("Square", "side", side)
        super().__init__(
            width=side,
            height=side,
            fillColor=fillColor,
            strokeColor=strokeColor,
            strokeWidth=strokeWidth,
            cornerRadius=cornerRadius,
        )


class HorizontalLine(Rectangle):
    """
    Horizontal Line
    """

    def __init__(
        self,
        length: wunumber = 3,
        strokeWidth: wunumber = 0.025,
        fillColor: paint = BLUE_A,
        strokeColor: rgba = TRANSPARENT,
        rounded: bool = True,
    ):
        super().__init__(
            width=length,
            height=strokeWidth,
            fillColor=fillColor,
            strokeColor=strokeColor,
            strokeWidth=strokeWidth / 3,
            cornerRadius=100 if rounded else 0,
        )

    @property
    def length(self):
        return self.width

    @length.setter
    def length(self, value: wnumber):
        self.width = value


class VerticalLine(Rectangle):
    """
    Vertical Line
    """

    def __init__(
        self,
        length: wunumber = 3,
        strokeWidth: wunumber = 0.025,
        fillColor: paint = BLUE_A,
        strokeColor: rgba = TRANSPARENT,
        rounded: bool = True,
    ):
        super().__init__(
            height=length,
            width=strokeWidth,
            fillColor=fillColor,
            strokeColor=strokeColor,
            strokeWidth=strokeWidth / 3,
            cornerRadius=100 if rounded else 0,
        )

    @property
    def length(self):
        return self.height

    @length.setter
    def length(self, value: wnumber):
        self.height = value
