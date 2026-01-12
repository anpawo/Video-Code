#!/usr/bin/env python3

from videocode.shader.ishader import FragmentShader
from videocode.ty import unumber


class gamma(FragmentShader):
    """
    Adjust the brightness of an `Input`.

    gamma < 1 -> gets darker

    gamma = 1 -> no change

    gamma > 1 -> gets lighter

    gamma must be `positive`.
    """

    def __init__(self, gamma: unumber = 1.0):
        self.gamma = gamma
