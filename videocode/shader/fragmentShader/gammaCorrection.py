#!/usr/bin/env python3

from videocode.shader.ishader import FragmentShader
from videocode.ty import unumber


class gammaCorrection(FragmentShader):
    """Gamma correction"""

    def __init__(self, gammaCorrection: unumber = 1.0):
        self.gammaCorrection = gammaCorrection
