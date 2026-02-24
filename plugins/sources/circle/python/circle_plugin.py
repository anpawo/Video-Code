from videocode.constants import RED
from videocode.input.shape.shape import Shape
from videocode.ty import rgba
from videocode.utils.decorators import inputCreation


class circle(Shape):
    @inputCreation
    def __init__(self, radius: int = 100, thickness: int = 5, color: rgba = RED, filled: bool = False):
        self.radius = radius
        self.thickness = thickness
        self.color = color
        self.filled = filled


def register(target):
    target["circle"] = circle
