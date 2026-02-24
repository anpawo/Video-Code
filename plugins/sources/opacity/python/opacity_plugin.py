from videocode.shader.ishader import FragmentShader
from videocode.ty import *


class opacity(FragmentShader):
    def __init__(self, opacity: unumber):
        self.opacity = opacity


def register(target):
    target["opacity"] = opacity
