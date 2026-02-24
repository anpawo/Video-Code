from videocode.shader.ishader import FragmentShader
from videocode.ty import *


class blur(FragmentShader):
    def __init__(self, strength: unumber = 1.0):
        self.strength = strength


def register(target):
    target["blur"] = blur
