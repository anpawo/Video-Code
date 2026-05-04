#!/usr/bin/env python3


from videocode import *
from videocode.input.offset.Offset import Offset
from videocode.input.sticky.Sticky import Sticky
from videocode.utils.decorators import autoProp, trackProps


class Arrow(Polygon):
    @trackProps
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

    @autoProp(Polygon.updatePoints)
    def length() -> wfloat: ...

    @autoProp(Polygon.updatePoints, getMod=lambda s, bw: s.length * 0.05 if bw is None else bw)
    def bodyWidth() -> wufloat: ...

    @autoProp(Polygon.updatePoints, getMod=lambda s, bl: s.length * 0.8 if bl is None else bl)
    def bodyLength() -> wufloat: ...

    @autoProp(Polygon.updatePoints, getMod=lambda s, ts: s.length * 0.2 if ts is None else ts)
    def tipLength() -> wufloat: ...

    @autoProp(Polygon.updatePoints, getMod=lambda s, th: s.length * 0.2 if th is None else th)
    def tipHeight() -> wufloat: ...

    @autoProp(Polygon.updatePoints, getMod=lambda s, bt: 0 if bt is None else bt)
    def bodyInTip() -> wufloat: ...


# class ArrowWithOffset(Group):
#     def __init__(
#         self,
#         length: wunumber = 1,
#         rounded=True,
#     ) -> None:
#         self.body = HorizontalLine(length=length, strokeWidth=length / 30, fillColor=WHITE, rounded=rounded)
#         self.tip = EquilateralTriangle(side=length / 5, strokeColor=TRANSPARENT, fillColor=WHITE, cornerRadius=rounded * 25)

#         super().__init__(
#             self.body,
#             Offset(self.tip, x=length / 2 * math.sqrt(3) / 2, y=0, r=90),
#         )

#         self.position().rotation(0)

# class AlignedArrow(Group):
#     """
#     Arrow that takes into account the changes of alignment.
#     """

#     def __init__(
#         self,
#         length: wunumber = 1,
#         rounded=True,
#     ) -> None:
#         self.body = HorizontalLine(length=length, strokeWidth=length / 25, fillColor=WHITE, rounded=rounded)
#         self.tip = EquilateralTriangle(side=length / 5, strokeColor=TRANSPARENT, fillColor=WHITE, cornerRadius=rounded * 25)

#         b = self.body

#         def tipPositionModifier(_, p: position, _s, _d):
#             angle = math.radians(b.meta.rotation)

#             p.x += (b.width / 2) * math.cos(angle)  # type: ignore # TODO:
#             p.y -= (b.width / 2) * math.sin(angle)  # type: ignore # TODO:

#         def tipAlignModifier(_, a: align, _s, _d):
#             a.x = 0.5
#             a.y = 0.5

#         def tipRotationCallback(i: Input, r: rotation, start: sec, duration: sec):
#             # Modifier
#             r.degree += 90

#             angle = math.radians(b.meta.rotation)
#             o.x = (0.5 - b.meta.align.x) * b.width * math.cos(angle) + (0.5 - b.meta.align.y) * b.height * math.sin(angle)
#             o.y = -(0.5 - b.meta.align.x) * b.width * math.sin(angle) + (0.5 - b.meta.align.y) * b.height * math.cos(angle)

#             i.apply(position(x=b.meta.position.x, y=b.meta.position.y), start=start, duration=duration)

#         self.cbTip = Sticky(
#             (o := Offset(self.tip, 0, 0, 0)),
#             [
#                 (position, tipPositionModifier),
#                 (align, tipAlignModifier),
#                 (rotation, tipRotationCallback),
#             ],
#         )

#         def bodyAlignModifier(i: Input, a: align, start: sec, duration: sec):
#             angle = math.radians(b.meta.rotation)
#             o.x = (0.5 - a.x if a.x is not None else i.meta.align.x) * b.width * math.cos(angle) + (0.5 - a.y if a.y is not None else i.meta.align.y) * b.height * math.sin(angle)
#             o.y = -(0.5 - a.x if a.x is not None else i.meta.align.x) * b.width * math.sin(angle) + (0.5 - a.y if a.y is not None else i.meta.align.y) * b.height * math.cos(angle)

#             o.apply(
#                 position(o._basePosition.x, o._basePosition.y),
#                 start=start,
#                 duration=duration,
#             )

#         self.cbBody = Sticky(
#             self.body,
#             [
#                 (align, bodyAlignModifier),
#             ],
#         )

#         super().__init__(
#             self.cbBody,
#             self.cbTip,
#         )

#         self.position().rotation(0)
