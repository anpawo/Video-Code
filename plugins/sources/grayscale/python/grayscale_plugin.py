from videocode.shader.ishader import FragmentShader
from videocode.ty import *


class grayscale(FragmentShader):
    def __init__(self) -> None: ...


def register(target):
    target["grayscale"] = grayscale
