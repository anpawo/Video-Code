#!/usr/bin/env python3

from __future__ import annotations

from videocode.input.interface.Group import _GROUP_T, Group
from videocode.input.input import Input
from videocode.shader.vertexShader.position import position
from videocode.ty import *
from videocode.constants import *

__all__ = ["XAlign"]


class XAlign(Group[_GROUP_T]):
    """
    Lay inputs out horizontally, `gap` apart, centered on the group position.

    Layout happens at construction so the rigid-body base snapshot is correct —
    position/scale/rotation applied to the group keep the members' spacing.
    """

    def __init__(self, gap: wnumber = 0.1, *inputs: Input):
        # To Fix when even numbers of inputs, i want them to be centered
        self.gap = gap
        half = len(inputs) // 2
        for i, input in enumerate(inputs):
            input.apply(position((i - half) * gap, 0))
        super().__init__(*inputs)
