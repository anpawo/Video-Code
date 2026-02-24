from videocode.shader.ishader import FragmentShader
from videocode.ty import *


class gamma(FragmentShader):
    def __init__(self, gamma: unumber = 1.0):
        self.gamma = gamma


def register(target):
    target["gamma"] = gamma
