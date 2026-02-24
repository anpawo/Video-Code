from videocode.input.input import Input
from videocode.utils.decorators import inputCreation


class image(Input):
    @inputCreation
    def __init__(self, filepath: str) -> None:
        self.filepath = filepath


def register(target):
    target["image"] = image
