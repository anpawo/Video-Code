#!/usr/bin/env python3

from __future__ import annotations

from videocode.constants import Self
from videocode.input.input import Input
from videocode.input.interface.Group import Group
from videocode.ty import *
from videocode.constants import *
from videocode.ty import Self

__all__ = ["YStack", "Paragraphe"]


class YStack(Group):
    def __init__(self, gap: number):
        self.curY: wnumber = 0
        self.lastHeight: wnumber = 0
        self.gap = gap
        super().__init__()

    def add(self, input: Input) -> Self:
        self.lastHeight = h = input.height
        localY = self.curY - h / 2
        input.position(self.meta.position.x, (self.meta.position.y or 0) + localY)
        self.inputs.append(input)
        return self

    def space(self, n: number) -> Self:
        self.curY -= n
        return self


class Paragraphe(YStack):
    def __init__(self, gap: number):
        super().__init__(gap)

    def newline(self) -> Self:
        return self.space(self.lastHeight + self.gap)

    def add(self, input: Input, addNewline=True) -> Self:
        super().add(input)
        self.waitForOthers()
        input.animateIn()
        if addNewline:
            return self.newline()
        return self
