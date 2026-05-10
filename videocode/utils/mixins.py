#!/usr/bin/env python3


from videocode.ty import rgba
from videocode.utils.decorators import autoProp


class _fillColor:

    @autoProp
    def fillColor() -> rgba: ...
