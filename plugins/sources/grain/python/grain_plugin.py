from videocode.shader.ishader import FragmentShader
from videocode.ty import *


class grain(FragmentShader):
    def __init__(self, amount: unumber):
        self.amount = amount


def register(target):
    target["grain"] = grain
