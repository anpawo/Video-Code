#!/usr/bin/env python3


from videocode import *


class Arrow(Group):
    def __init__(
        self,
        length: wunumber = 0.5,
    ) -> None:
        super().__init__(
            v := HorizontalLine(length=length, fillColor=WHITE),
            Offset(length * v.meta.align.x, 0, EquilateralTriangle(side=length / 5, strokeColor=TRANSPARENT, fillColor=WHITE)).rotate(90),
        )
