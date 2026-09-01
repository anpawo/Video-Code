#!/usr/bin/env python3

from __future__ import annotations

from videocode.shader.ishader import *


class rotation(VertexShader):
    _rigidKind = 2
    """
    `Rotation` is set to degree.

    `about` places the point the turn happens around, in world units. Left
    None, a group derives it from its `align` — a fraction of its own bounding
    box, which can only ever name a point the content already has.
    """

    def __init__(self, degree: number, *, about: maybe[v2] = None):
        self.degree = degree
        #: Where the turn happens. None = the centre the group derives from its
        #: `align`, which is the only answer this engine used to have.
        self.about = about

    def autodestroy(self, i: Input) -> bool:
        return i.meta.rotation == self.degree

    def modify(self, i: Input):
        i.meta.rotation = self.degree
