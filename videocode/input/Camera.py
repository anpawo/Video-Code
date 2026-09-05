#!/usr/bin/env python3

from __future__ import annotations

# Imported precisely (not `from videocode import *`) because this module is
# pulled in during package init via input/_inputs.py — a star import of the
# package would be circular.
from typing import Self

from videocode.constants import SINGLE_FRAME, WORLD_HEIGHT, WORLD_WIDTH
from videocode.context import Context, Metadata
from videocode.input.input import Input
from videocode.shader.ishader import Effect, GroupEffect, IShader
from videocode.shader.vertexShader.scale import scale as _scaleShader
from videocode.ty import frame, maybe, number, sec, wnumber
from videocode.utils.decorators import prop


class Camera(Input):
    """
    The scene's viewport: where the picture is looked at from, and how close.

    There is one per scene and it is already there — `camera`, exported by the
    package. It moves like anything else, through the same claims every other
    property travels on:

        camera.moveTo(x=3, duration=1)      # pan: the picture slides left
        camera.over(duration=1).zoom = 2    # magnify about what it looks at
        camera.position(0, 0)               # back to the middle, at once

    `position` is the world point the camera looks at — what lands in the
    middle of the frame — so moving the camera right moves the picture left.
    `zoom` is a magnification about that point: 2 shows half as much, twice as
    big. It is one matrix in the vertex stage, not a composite of the scene, so
    it costs nothing per frame and nothing is ever flattened.

    Anything that must ignore all of it — a subtitle, a watermark — says so for
    itself with `Input.pinToFrame()`.

    A scene that never touches the camera never gives it a slot in the stack,
    so it renders exactly as it did before this existed.
    """

    cppName = "Camera"

    def __init__(self) -> None:
        self._zoom: number = 1

    # A camera is not turned: vertices reach the GPU in NDC, which is not
    # square, so a rotation applied there would shear the scene rather than
    # turn it. Rotating the picture would have to happen in pixels — a
    # different feature, and not one anybody asked for.

    @property
    def width(self) -> wnumber:
        """How much world the frame shows across, at the current zoom."""
        return WORLD_WIDTH / self.zoom

    @property
    def height(self) -> wnumber:
        """How much world the frame shows down, at the current zoom."""
        return WORLD_HEIGHT / self.zoom

    def _applyZoom(self) -> None:
        # Through the ordinary `scale` claim, with whatever timing the
        # assignment carried (`over()` sets the pending window on the meta
        # before it assigns) — so a zoom is animated by the same code that
        # animates a shape's size.
        self.apply(
            _scaleShader(self._zoom, self._zoom),
            start=self.meta.pendingStart,
            duration=self.meta.pendingDuration,
            offset=self.meta.pendingOffset,
        )

    @prop(onSet=_applyZoom)
    def zoom(self, _: number) -> number:
        """
        Magnification about the point the camera looks at. 1 is life size.

        Read off `meta.scale` rather than the stored value, so `camera.zoom`
        still answers truthfully after a `camera.scaleTo(...)` — one piece of
        state, not two names for it.
        """
        return self.meta.scale.x

    def apply(self, *shaders: IShader | Effect | GroupEffect, start: sec = 0, duration: sec = SINGLE_FRAME, offset: maybe[frame] = None) -> Self:
        """
        Claim a channel of the camera — its first claim is what puts it in the
        stack.

        Registered here rather than at import so a scene that never mentions
        the camera reaches C++ exactly as it did before there was one, down to
        the input indices. Everything else is `Input.apply`.
        """
        if self.meta.index is None:
            self.meta.index = Context.getIndex()
            # Deliberately not appended to `Context.metas`: that register
            # answers "what is the highest layer in this scene", and the camera
            # is never drawn on any layer.
            Context.create(self.meta.index, self.cppName, {})
        return super().apply(*shaders, start=start, duration=duration, offset=offset)

    def _reset(self) -> None:
        # Called by serialize._resetContext, next to the other state that lives
        # on a class rather than on Context. One process renders several shapes
        # in a row (`--for youtube,tiktok`) and the editor bakes on every
        # gesture; a camera left where the last run parked it would pan a scene
        # that never asked to be panned.
        with Context.noRegister():
            self.meta = Metadata()
        self._zoom = 1

    def __str__(self) -> str:
        return f"Camera(looking at {self.meta.position}, zoom {self.zoom})"


# The scene's one camera. Built with no slot of its own (Context.noRegister),
# so importing the package costs nothing to a scene that never pans.
with Context.noRegister():
    camera = Camera()
