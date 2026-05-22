#!/usr/bin/env python3


from videocode.constants import rgba
from videocode.input.interface.Group import Group
from videocode.input.interface.Offset import Offset
from videocode.input.shape.Rectangle import Rectangle
from videocode.input.shape.text.Text import Text
from videocode.constants import *
from videocode.shader.vertexShader.position import position
from videocode.utils.classutils import At
from videocode.utils.decorators import prop
from videocode.utils.funcutils import darken, lighten


class Button(Group):

    def __init__(
        self,
        width: wnumber,
        height: wnumber,
        text: str,
        color: rgba,
    ):
        self.color = color

        self.isHovered = False

        self.rect = Rectangle(
            width=width,
            height=height,
            fillColor=darken(RED_B),
            strokeColor=color,
            cornerRadius=30,
            strokeWidth=height / 40,
        )
        self.text = Text(
            text=text,
            fillColor=color,
            fontSize=height / 2.85,
        )

        super().__init__(
            self.rect,
            self.text,
        )

    def onHover(self, pos: position, s: sec, d: sec, o: frame):
        """
        Callback to give to a cursor for example.
        """
        self.isHovered = self.rect.contains(pos.x, pos.y)
        self.color = self.color @ At(s, d, o)

    @prop()
    def color() -> rgba: ...

    @color.setter
    def colorSetter(self, value: rgba) -> None:
        self.rect.fillColor = lighten(value) if self.isHovered else darken(value)
        self.rect.strokeColor = value
        self.text.fillColor = value


class RedButton(Button):
    def __init__(self, width: wnumber, height: wnumber, text: str):
        super().__init__(width, height, text, RED_B)


class GreenButton(Button):
    def __init__(self, width: wnumber, height: wnumber, text: str):
        super().__init__(width, height, text, GREEN_A)


class BlueButton(Button):
    def __init__(self, width: wnumber, height: wnumber, text: str):
        super().__init__(width, height, text, BLUE_C)
