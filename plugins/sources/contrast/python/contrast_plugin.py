from videocode.shader.ishader import FragmentShader
from videocode.ty import *


class contrast(FragmentShader):
    def __init__(self, amount: int8):
        self.amount = amount


def register(target):
    target["contrast"] = contrast
