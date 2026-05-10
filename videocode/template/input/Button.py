#!/usr/bin/env python3


from videocode.constants import rgba
from videocode.input.group.Group import Group
from videocode.input.shape.Rectangle import Rectangle
from videocode.input.text.Text import Text
from videocode.constants import *
from videocode.utils.decorators import autoProp, trackProps, prop


class Button(Group):

    @trackProps
    def __init__(
        self,
        width: wnumber,
        height: wnumber,
        text: str,
        color: rgba,
    ):
        self.isHovered = False

        self.rect = Rectangle(
            width=width,
            height=height,
            fillColor=self.darken(RED_B),
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

    @autoProp
    def isHovered() -> bool: ...

    @prop()
    def color() -> rgba: ...

    @color.setter
    def colorSetter(self, value: rgba) -> None:
        with self.rect:
            self.rect.fillColor = self.lighten(value) if self.isHovered else self.darken(value)
            self.rect.strokeColor = value
        with self.text:
            self.text.fillColor = value

    def darken(self, c: rgba) -> rgba:
        return c | 0.75 | BLACK | (BLACK | 0.7)

    def lighten(self, c: rgba) -> rgba:
        return c | 0.75 | BLACK | GRAY_10


class RedButton(Button):
    def __init__(self, width: wnumber, height: wnumber, text: str):
        super().__init__(width, height, text, RED_B)


class GreenButton(Button):
    def __init__(self, width: wnumber, height: wnumber, text: str):
        super().__init__(width, height, text, GREEN_A)


class BlueButton(Button):
    def __init__(self, width: wnumber, height: wnumber, text: str):
        super().__init__(width, height, text, BLUE_C)
