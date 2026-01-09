#!/usr/bin/env python3

from videocode.shader.ishader import FragmentShader
from videocode.ty import number


class contrast(FragmentShader):
    """Adjust contrast (-255..255)."""

    def __init__(self, value: number = 0):
        self.value = value
