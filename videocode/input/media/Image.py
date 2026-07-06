#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import os
import subprocess
import urllib.parse

from PIL import Image as PILImage

from videocode.input.shape.Polygon import *
from videocode.constants import WORLD_TO_SCREEN_RATIO


__all__ = [
    "Image",
    "WebImage",
]


class Image(Polygon):
    cppName = "Image"
    cppAttrs = Polygon.cppAttrs | {"filepath", "uvMapping", "uvAngle"}

    def __init__(
        self,
        filepath: str,
        width: maybe[wunumber] = None,
        height: maybe[wunumber] = None,
        cornerRadius: percent = 0,
        strokeColor: rgba = TRANSPARENT,
        strokeWidth: wufloat = 0,
        uvMapping: UVMapping = UVMapping.STRETCH,
        uvAngle: wufloat = 0,
    ):
        """
        `uvMapping` controls how the texture is wrapped onto the shape —
        see the `UVMapping` enum for the mode semantics; `uvAngle` (degrees)
        rotates the angular origin of the polar modes.
        """
        self.filepath = filepath
        self.uvMapping = uvMapping
        self.uvAngle = uvAngle

        # Rounding/stroking needs a known shape — if the caller didn't give
        # one, fall back to the image's natural size (read from its header,
        # no full decode).
        if cornerRadius and width is None and height is None:
            with PILImage.open(filepath) as img:
                width, height = img.size
            width /= WORLD_TO_SCREEN_RATIO
            height /= WORLD_TO_SCREEN_RATIO

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


CACHE_DIR = "webimage"


class WebImage(Image):
    def __init__(self, url: str):
        os.makedirs(CACHE_DIR, exist_ok=True)

        parsed = urllib.parse.urlparse(url)
        ext = os.path.splitext(parsed.path)[1] or ".png"
        urlHash = hashlib.md5(url.encode()).hexdigest()
        filepath = os.path.join(CACHE_DIR, urlHash + ext)

        if not os.path.exists(filepath):
            result = subprocess.run(
                ["curl", "-L", "--ssl-reqd", "-o", filepath, url],
                capture_output=True,
            )
            if result.returncode != 0:
                raise RuntimeError(f"Curl Error: {result.stderr.decode()}")

        super().__init__(
            filepath=filepath,
        )
