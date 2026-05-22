#!/usr/bin/env python3


import hashlib
import os
import subprocess
import urllib.parse


from videocode.utils.decorators import inputCreation
from videocode.input.input import *


__all__ = [
    "Image",
    "WebImage",
]


class Image(Input):
    cppName = "Image"
    cppAttrs = {
        "filepath",
    }

    @inputCreation
    def __init__(
        self,
        filepath: str,
    ):
        self.filepath = filepath


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
