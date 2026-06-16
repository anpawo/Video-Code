#!/usr/bin/env python3

"""
Assertion-based smoke tests for Image/Video `uvMapping`/`uvAngle` (#127,
"Textured radial/conic gradient fills") — verifies the Create-stack entry
carries the UV mapping mode + angle that BezierPath::buildPath() reads to
choose between bbox-stretch (default) and polar (radial/conic) UVs for
textured fills.
Run directly: `python3 test/uvmapping_test.py`
"""

import sys

sys.path.insert(0, ".")

from videocode import Image, Video
from videocode.context import Context

failures: list[str] = []


def check(label: str, condition: bool):
    if condition:
        print(f"  ok   {label}")
    else:
        print(f"  FAIL {label}")
        failures.append(label)


print("Image — uvMapping/uvAngle defaults")
img = Image("wb.png", width=1, height=1)
entry = Context.stack[img.meta.index][-1]
check("default uvMapping is stretch", entry["args"]["uvMapping"] == "stretch")
check("default uvAngle is 0", entry["args"]["uvAngle"] == 0)

print("Image — uvMapping/uvAngle overrides")
img2 = Image("wb.png", width=1, height=1, uvMapping="radial", uvAngle=45)
entry2 = Context.stack[img2.meta.index][-1]
check("uvMapping radial", entry2["args"]["uvMapping"] == "radial")
check("uvAngle 45", entry2["args"]["uvAngle"] == 45)

img3 = Image("wb.png", width=1, height=1, uvMapping="conic")
entry3 = Context.stack[img3.meta.index][-1]
check("uvMapping conic", entry3["args"]["uvMapping"] == "conic")

print("Video — uvMapping/uvAngle defaults and overrides")
vid = Video("test.mp4", width=1, height=1)
ventry = Context.stack[vid.meta.index][-1]
check("default uvMapping is stretch", ventry["args"]["uvMapping"] == "stretch")
check("default uvAngle is 0", ventry["args"]["uvAngle"] == 0)

vid2 = Video("test.mp4", width=1, height=1, uvMapping="conic", uvAngle=90)
ventry2 = Context.stack[vid2.meta.index][-1]
check("uvMapping conic", ventry2["args"]["uvMapping"] == "conic")
check("uvAngle 90", ventry2["args"]["uvAngle"] == 90)


# ── summary ──────────────────────────────────────────────────────────────────
print()
if failures:
    print(f"{len(failures)} FAILURE(S):")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)
else:
    print("All checks passed.")
