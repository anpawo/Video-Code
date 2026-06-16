#!/usr/bin/env python3

from __future__ import annotations

import subprocess

from videocode.input.shape.Polygon import *
from videocode.constants import WORLD_TO_SCREEN_RATIO


__all__ = ["Video"]


class Video(Polygon):
    cppName = "Video"
    cppAttrs = Polygon.cppAttrs | {"filepath", "cuts", "uvMapping", "uvAngle"}

    def __init__(
        self,
        filepath: str,
        cuts: list[frame | tuple[frame, frame]] = [],
        startFrame: frame = 0,
        endFrame: maybe[frame] = None,
        width: maybe[wunumber] = None,
        height: maybe[wunumber] = None,
        cornerRadius: percent = 0,
        strokeColor: rgba = TRANSPARENT,
        strokeWidth: wufloat = 0,
        uvMapping: Literal["stretch", "radial", "conic"] = "stretch",
        uvAngle: wufloat = 0,
    ) -> None:
        """
        `cuts` are ranges of source-video frames to skip during playback —
        either a single frame index `n` (shorthand for `(n, n + 1)`) or a
        `(start, end)` pair cutting `[start, end)`.

        `startFrame`/`endFrame` restrict playback to the source frame range
        `[startFrame, endFrame)` — shorthand for cutting everything outside
        that range (`endFrame=None` plays to the end of the source).

        `uvMapping` controls how the texture is wrapped onto the shape:

        - `"stretch"` (default): bbox-normalized UVs — the texture is
          stretched to the shape's bounding box.
        - `"radial"`/`"conic"`: polar UVs around the bbox center, mirroring
          `RadialGradient`/`ConicGradient`'s center/angle convention.
          `uvAngle` (degrees) rotates the angular origin.
        """
        self.filepath = filepath
        self.uvMapping = uvMapping
        self.uvAngle = uvAngle
        cuts = [c if isinstance(c, tuple) else (c, c + 1) for c in cuts]
        if startFrame:
            cuts.append((0, startFrame))
        if endFrame is not None:
            # the C++ side clamps `end` to the source's actual frame count,
            # so an over-large sentinel cuts everything past `endFrame`.
            cuts.append((endFrame, 2**31 - 1))
        self.cuts = cuts

        # Rounding/stroking needs a known shape — if the caller didn't give
        # one, fall back to the video's natural frame size (ffprobe metadata,
        # no frame decode).
        if cornerRadius and width is None and height is None:
            out = subprocess.run(
                ["ffprobe", "-v", "error", "-select_streams", "v:0",
                 "-show_entries", "stream=width,height", "-of", "csv=p=0", filepath],
                capture_output=True, text=True, check=True,
            )
            w, h = out.stdout.strip().split(",")
            width = float(w) / WORLD_TO_SCREEN_RATIO
            height = float(h) / WORLD_TO_SCREEN_RATIO

        self.width = width
        self.height = height

        super().__init__(
            vertices=self.generateVertices(),
            fillColor=TRANSPARENT,
            strokeColor=strokeColor,
            strokeWidth=strokeWidth,
            cornerRadius=cornerRadius,
        )

    def generateVertices(self) -> list[point]:
        if self.width is None or self.height is None:
            return []
        return [(0, 0), (self.width, 0), (self.width, self.height), (0, self.height)]

    @prop(onSet=Polygon.updatePoints)
    def width() -> maybe[wunumber]: ...

    @prop(onSet=Polygon.updatePoints)
    def height() -> maybe[wunumber]: ...
