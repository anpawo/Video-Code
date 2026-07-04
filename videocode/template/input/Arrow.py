#!/usr/bin/env python3

from __future__ import annotations

from videocode import *
from videocode.utils.decorators import prop


class Arrow(Polygon):
    def __init__(
        self,
        length: wfloat = 1,
        bodyLength: maybe[wufloat] = None,
        bodyWidth: maybe[wufloat] = None,
        tipLength: maybe[wufloat] = None,
        tipHeight: maybe[wufloat] = None,
        bodyInTip: maybe[wufloat] = None,
        fillColor: rgba = WHITE,
        strokeColor: rgba = TRANSPARENT,
        strokeWidth: wufloat = 0,
        cornerRadius: percent = 0,
    ):
        self.length = length
        self.bodyWidth = bodyWidth
        self.bodyLength = bodyLength
        self.tipLength = tipLength
        self.tipHeight = tipHeight
        self.bodyInTip = bodyInTip

        super().__init__(
            vertices=self.generateVertices(),
            fillColor=fillColor,
            strokeColor=strokeColor,
            strokeWidth=strokeWidth,
            cornerRadius=cornerRadius,
            sharpCorners={1, 5},
        )

    def generateVertices(self) -> list[point]:
        halfBodyWidth = self.bodyWidth / 2
        halfTipHeight = self.tipHeight / 2
        bodyLength = self.bodyLength
        tipLength = self.tipLength
        bodyInTip = self.bodyInTip

        return [
            (0, halfBodyWidth),
            (bodyLength + bodyInTip, halfBodyWidth),
            (bodyLength, halfBodyWidth + halfTipHeight),
            (bodyLength + tipLength, 0),
            (bodyLength, -halfBodyWidth - halfTipHeight),
            (bodyLength + bodyInTip, -halfBodyWidth),
            (0, -halfBodyWidth),
        ]

    @prop(onSet=Polygon.updatePoints)
    def length() -> wfloat: ...

    @prop(onSet=Polygon.updatePoints)
    def bodyWidth(self, v: maybe[wufloat]) -> wfloat:
        return Maybe(v) | self.length * 0.05

    @prop(onSet=Polygon.updatePoints)
    def bodyLength(self, v: maybe[wufloat]) -> wfloat:
        return Maybe(v) | self.length * 0.8

    @prop(onSet=Polygon.updatePoints)
    def tipLength(self, v: maybe[wufloat]) -> wfloat:
        return Maybe(v) | self.length * 0.2

    @prop(onSet=Polygon.updatePoints)
    def tipHeight(self, v: maybe[wufloat]) -> wfloat:
        return Maybe(v) | self.length * 0.2

    @prop(onSet=Polygon.updatePoints)
    def bodyInTip(self, v: maybe[wufloat]) -> wfloat:
        return Maybe(v) | 0


class DoubleArrow(Polygon):
    def __init__(
        self,
        length: wfloat = 1,
        bodyLength: maybe[wufloat] = None,
        bodyWidth: maybe[wufloat] = 0.025,
        tipLength: maybe[wufloat] = 0.1,
        tipHeight: maybe[wufloat] = 0.1,
        bodyInTip: maybe[wufloat] = None,
        relative: bool = False,
        fillColor: rgba = WHITE,
        strokeColor: rgba = TRANSPARENT,
        strokeWidth: wufloat = 0,
        cornerRadius: percent = 0,
    ):
        self._relative = relative
        self.length = length
        self.bodyWidth = bodyWidth
        self.bodyLength = bodyLength
        self.tipLength = tipLength
        self.tipHeight = tipHeight
        self.bodyInTip = bodyInTip

        super().__init__(
            vertices=self.generateVertices(),
            fillColor=fillColor,
            strokeColor=strokeColor,
            strokeWidth=strokeWidth,
            cornerRadius=cornerRadius,
            sharpCorners={2, 3, 7, 8},
        )

    def generateVertices(self) -> list[point]:
        halfBodyWidth = self.bodyWidth / 2
        halfTipHeight = self.tipHeight / 2
        bodyInTip = self.bodyInTip
        tipLength = self.tipLength
        bodyLength = self.bodyLength

        return [
            (0, 0),
            (tipLength, halfBodyWidth + halfTipHeight),
            (tipLength - bodyInTip, halfBodyWidth),
            (tipLength + bodyLength + bodyInTip, halfBodyWidth),
            (tipLength + bodyLength, halfBodyWidth + halfTipHeight),
            (tipLength + bodyLength + tipLength, 0),
            (tipLength + bodyLength, -halfBodyWidth - halfTipHeight),
            (tipLength + bodyLength + bodyInTip, -halfBodyWidth),
            (tipLength - bodyInTip, -halfBodyWidth),
            (tipLength, -halfBodyWidth - halfTipHeight),
        ]

    @prop(onSet=Polygon.updatePoints)
    def length() -> wfloat: ...

    def _scl(self, v: wufloat) -> wufloat:
        return self.length * v if self._relative else v

    @prop(onSet=Polygon.updatePoints)
    def bodyWidth(self, v: maybe[wufloat]) -> wfloat:
        return self._scl(Maybe(v) | 0.05)

    @prop(onSet=Polygon.updatePoints)
    def bodyLength(self, v: maybe[wufloat]) -> wfloat:
        return Maybe(v) | max(self.length - 2 * self.tipLength, 0)

    @prop(onSet=Polygon.updatePoints)
    def tipLength(self, v: maybe[wufloat]) -> wfloat:
        return self._scl(Maybe(v) | 0.1)

    @prop(onSet=Polygon.updatePoints)
    def tipHeight(self, v: maybe[wufloat]) -> wfloat:
        return self._scl(Maybe(v) | 0.1)

    @prop(onSet=Polygon.updatePoints)
    def bodyInTip(self, v: maybe[wufloat]) -> wfloat:
        return Maybe(v) | 0


class Cursor(Arrow):
    def __init__(self):
        super().__init__(
            fillColor=BLACK,
            strokeColor=WHITE,
            strokeWidth=0.0125,
            bodyLength=0.05,
            bodyWidth=0.1 * 0.2,
            bodyInTip=0.015,
            tipLength=0.15,
            tipHeight=0.085,
            cornerRadius=50,
        )

        self.rotation(-112.5)
