from videocode.constants import GREEN
from videocode.input.shape.shape import Shape
from videocode.ty import degree, rgba, wufloat
from videocode.utils.decorators import inputCreation


class rectangle(Shape):
    @inputCreation
    def __init__(self, width: wufloat = 3, height: wufloat = 2, thickness: wufloat = 0.05, color: rgba = GREEN, cornerRadius: degree = 0, filled: bool = False):
        self.width = width
        self.height = height
        self.thickness = thickness
        self.color = color
        self.cornerRadius = cornerRadius
        self.filled = filled


def register(target):
    target["rectangle"] = rectangle
