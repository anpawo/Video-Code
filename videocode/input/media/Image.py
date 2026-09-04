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


def _fitToRatio(
    width: maybe[wunumber], height: maybe[wunumber], natW: number, natH: number
) -> tuple[wunumber, wunumber]:
    """
    The size a media file is drawn at when the caller left a number out: one
    dimension given fixes the other through the source's own proportions,
    neither given falls back to its natural pixel size. Shared with `Video`,
    which asks ffprobe for `natW`/`natH` where this file asks PIL.
    """
    if width is not None:
        return width, width * natH / natW
    if height is not None:
        return height * natW / natH, height
    return natW / WORLD_TO_SCREEN_RATIO, natH / WORLD_TO_SCREEN_RATIO


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

        `width`/`height` together stretch the picture to that exact box;
        giving only one derives the other from the file's aspect ratio, and
        giving neither draws it at its natural pixel size.
        """
        self.filepath = filepath
        self.uvMapping = uvMapping
        self.uvAngle = uvAngle

        # A shape needs both numbers, so the file's header answers (no full
        # decode) whenever one is missing: one dimension given fixes the other
        # through the image's own proportions, neither given is its natural
        # size. The bare case used to skip the read and leave C++ to draw the
        # pixel quad on its own — which left Python with no size at all, so a
        # group could not find its pivot around it and nothing could be drawn
        # around it (X2).
        if width is None or height is None:
            with PILImage.open(filepath) as img:
                natW, natH = img.size
            width, height = _fitToRatio(width, height, natW, natH)

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
                # `--proto '=https'`, not `--ssl-reqd`: the latter only means
                # anything to FTP, IMAP, POP3, SMTP and LDAP (man curl), so it
                # was a flag that read as "require TLS" and enforced nothing —
                # `WebImage("http://…")` downloaded in the clear. The redirect
                # form matters as much as the first hop, since `-L` follows.
                ["curl", "-L", "--proto", "=https", "--proto-redir", "=https", "-o", filepath, url],
                capture_output=True,
            )
            if result.returncode != 0:
                raise RuntimeError(f"Curl Error: {result.stderr.decode()}")

        super().__init__(
            filepath=filepath,
        )
