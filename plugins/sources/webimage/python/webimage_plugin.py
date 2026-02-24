from videocode.input.input import Input
from videocode.utils.decorators import inputCreation
from videocode.ty import url


class webImage(Input):
    @inputCreation
    def __init__(self, url: url):
        self.url = url


def register(target):
    target["webImage"] = webImage
