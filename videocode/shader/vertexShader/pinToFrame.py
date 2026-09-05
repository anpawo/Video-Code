#!/usr/bin/env python3

from __future__ import annotations

from videocode.shader.ishader import *


class pinToFrame(VertexShader):
    """
    Draw an `Input` in FRAME space — the scene `camera` never moves it.

    Presence is the whole signal; there are no arguments. The renderers key off
    `meta.pinnedToFrame` and push the identity camera for this mesh, so a
    subtitle, a watermark or a lower third holds still while the picture behind
    it pans and zooms.

    Users don't apply this directly — `Input.pinToFrame()` does, and it reaches
    a `Group`'s members too.
    """

    def __init__(self):
        pass

    def autodestroy(self, i: Input) -> bool:
        """Already pinned — a second application would write nothing new."""
        return i.meta.pinnedToFrame

    def modify(self, i: Input):
        """Pin it: from this frame on the camera passes it by."""
        i.meta.pinnedToFrame = True
