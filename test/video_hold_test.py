#!/usr/bin/env python3
"""
`Video(holds=[(at, seconds)])` stops the clip on one image, then plays on.

The clip is made for the check: its brightness is its own frame number, and a
tone runs under it. Held one second at one second, the rendered film is three
seconds long, the picture stops climbing for a second then climbs on from the
same image, and the tone is silent over exactly that second.

Run directly: `python3 test/video_hold_test.py`
"""

import re
import subprocess
import sys
import tempfile

sys.path.insert(0, ".")
sys.path.insert(0, "test")

from helpers import check, needsRenderer, needsTool, section, summary

from videocode import Video
from videocode.serialize import _resetContext

if not needsTool("ffmpeg", "the clip is made with it"):
    summary()
    sys.exit(0)

work = tempfile.mkdtemp(prefix="vc-hold-")
clip = f"{work}/ramp.mp4"
# Brightness = 16 + 3 × frame: 60 frames climb from 16 to 193, one step per frame.
subprocess.run(["ffmpeg", "-v", "error", "-y",
                "-f", "lavfi", "-i", "color=c=black:s=320x180:r=30:d=2,format=gray,geq=lum='16+3*N'",
                "-f", "lavfi", "-i", "sine=f=440:d=2",
                "-c:v", "libx264", "-qp", "0", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", clip], check=True)

# ---------------------------------------------------------------------------
section("the scene side: a hold lengthens the clip, and is refused when it cannot be")

_resetContext()
held = Video(clip, holds=[(1.0, 1.0)])
check(f"the clip ends a second later (end {held.end})", abs(held.end - 3.0) < 1 / 30)
check("the hold is written in frames", held.holds == [(30, 30)])
for bad in ((-1, 1), (1, 0)):
    try:
        _resetContext()
        Video(clip, holds=[bad])
        refused = False
    except ValueError:
        refused = True
    check(f"holds={[bad]} is refused", refused)

if not needsRenderer("the render is the proof"):
    summary()
    sys.exit(0)

# ---------------------------------------------------------------------------
section("the render: the picture stops, then climbs on from the same image")

scene, out = f"{work}/scene.py", f"{work}/held.mp4"
with open(scene, "w") as f:
    f.write(f"from videocode import *\nVideo({clip!r}, width=W, height=H, holds=[(1.0, 1.0)])\n")
subprocess.run(["./video-code", "--file", scene, "--generate", out, "--width", "320", "--height", "180"],
               check=True, capture_output=True, text=True)

said = subprocess.run(["ffmpeg", "-i", out, "-vf", "signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=-",
                       "-f", "null", "-"], capture_output=True, text=True).stdout
luma = [float(v) for v in re.findall(r"YAVG=([\d.]+)", said)]
check(f"the film is three seconds (got {len(luma)} frames)", 89 <= len(luma) <= 91)
before, hold, after = luma[5:28], luma[32:58], luma[62:88]
check("before the hold it climbs", all(b > a for a, b in zip(before, before[1:])))
check(f"over the hold it stays put (spread {max(hold) - min(hold):.2f})", max(hold) - min(hold) < 1.0)
check(f"after it, it climbs on from where it stopped ({luma[62]:.1f}, just above the hold's {hold[0]:.1f})",
      0 < luma[62] - hold[0] < 12 and all(b > a for a, b in zip(after, after[1:])))

# ---------------------------------------------------------------------------
section("the sound: silent over the hold, and in step after it")

quiet = subprocess.run(["ffmpeg", "-i", out, "-af", "silencedetect=n=-40dB:d=0.3", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
starts = [float(v) for v in re.findall(r"silence_start: ([\d.]+)", quiet)]
ends = [float(v) for v in re.findall(r"silence_end: ([\d.]+)", quiet)]
check(f"one silence, from 1 s to 2 s (starts {starts}, ends {ends})",
      len(starts) >= 1 and abs(starts[0] - 1.0) < 0.1 and len(ends) >= 1 and abs(ends[0] - 2.0) < 0.1)

summary()
