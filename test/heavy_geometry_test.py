#!/usr/bin/env python3
"""
A frame with more geometry than the renderer's buffers first hold still renders.

Twelve rows of stroked text are about 500 glyphs, past the 262 144 vertices the
geometry buffers were made for: the upload wrote past their end, a segfault for
a .png and a bus error for an .mp4 (issue #362). The buffers now grow to fit.

Run directly: `python3 test/heavy_geometry_test.py`
"""

import subprocess
import sys
import tempfile

sys.path.insert(0, ".")
sys.path.insert(0, "test")

from helpers import check, needsRenderer, section, summary

if not needsRenderer("the render is the proof"):
    summary()
    sys.exit(0)

work = tempfile.mkdtemp(prefix="vc-heavy-")
scene, out = f"{work}/scene.py", f"{work}/rows.png"
with open(scene, "w") as f:
    f.write(
        "from videocode import *\n"
        "for i in range(12):\n"
        "    Text('The quick brown fox jumps over the lazy dog', fontSize=0.45, fillColor=BLUE_C,\n"
        "         strokeColor=WHITE, strokeWidth=0.02).position(x=-1, y=4 - i * 0.7).moveTo(x=1, start=0, duration=4)\n"
    )

# ---------------------------------------------------------------------------
section("twelve rows of moving stroked text")

run = subprocess.run(["./video-code", "--file", scene, "--generate", out, "--width", "480", "--height", "270"],
                     capture_output=True, text=True)
check(f"the render exits cleanly (exit {run.returncode})", run.returncode == 0)

import cv2

image = cv2.imread(out, cv2.IMREAD_GRAYSCALE)
check("the image is written", image is not None)
if image is not None:
    # The last row sits at y = -3.7 of a 9-unit-high frame: 245 px down of 270.
    lastRow = image[235:260, :]
    check(f"the last row is drawn (brightest {lastRow.max()})", lastRow.max() > 200)

summary()
