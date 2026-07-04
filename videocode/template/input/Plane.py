#!/usr/bin/env python3

from __future__ import annotations

from videocode import *
from videocode.template.input.CompoundPolygon import CompoundPolygon


class Plane(Group):
    def __init__(
        self,
        # center=False,
        margin: wnumber = 2,
    ) -> None:
        transparent = 0.05
        self._margin = margin

        step = 1 / 3
        w = WORLD_WIDTH + 2 * margin
        h = WORLD_HEIGHT + 2 * margin
        # Background is 1 unit larger on each side so its edge never enters the
        # viewport even at full drift.

        fill_color: rgba = WHITE | transparent
        with Context.noRegister():
            v_lines = [
                VerticalLine(
                    length=h + 2,
                    strokeWidth=0.01,
                    rounded=False,
                    fillColor=fill_color,
                ).position(x=i, y=0, offset=0)
                for i in floatRange(w / -2, w / 2 + step, step)
            ]
            h_lines = [
                HorizontalLine(
                    length=w + 2,
                    strokeWidth=0.01,
                    rounded=False,
                    fillColor=fill_color,
                ).position(x=0, y=i, offset=0)
                for i in floatRange(-h / 2 - step, h / 2 + step, step)
            ]

        with Context.noHiding():
            self.bg = Rectangle(width=w + 2, height=h + 2, fillColor=BLUE_B, strokeColor=TRANSPARENT)
            self.grid = CompoundPolygon(*v_lines, *h_lines)
            # self.dot = Dot() if center else None

            super().__init__(
                self.bg,
                self.grid,
                # *([self.dot] if center else []),
            )

        # The grid (and its background rectangle) shouldn't be considered
        # part of the layer stack — sendToBack/bringToFront/etc. should treat
        # user shapes as the whole scene, not get pushed behind/in front of it.
        self.background(offset=0)

    def drift(
        self,
        dx: wnumber = -0.5,
        dy: wnumber = 0.25,
        duration: maybe[sec] = None,
    ) -> Self:
        self.grid.drift(dx, dy, duration)
        return self
