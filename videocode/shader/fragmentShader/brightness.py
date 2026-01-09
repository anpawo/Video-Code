#!/usr/bin/env python3

from videocode.shader.ishader import FragmentShader
from videocode.ty import number


class brightness(FragmentShader):
    """Adjust brightness by adding a value to RGB channels."""

    def __init__(self, value: number = 0):
        self.value = value
