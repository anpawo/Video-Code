from videocode.shader.ishader import FragmentShader
from videocode.ty import *


class brightness(FragmentShader):
    def __init__(self, amount: int8):
        self.amount = amount


def register(target):
    target["brightness"] = brightness
