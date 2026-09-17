#!/usr/bin/env python3
"""
`waitFor(video)` waits for the clip's last image, not for its last effect:
a 3.5 s clip with a 0.6 s pop on it used to release the waiter at 0.6 s.
"""
import json
import subprocess
import sys

sys.path.insert(0, ".")

import videocode.serialize as serialize  # noqa: E402

SCENE = """from videocode import *
from videocode.template.effect.other.popIn import popIn

clip = Video("marius.mov", width=6).opacity(0)
clip.apply(popIn(duration=0.6))

merci = Text("Merci").opacity(0)
merci.waitFor(clip).fadeIn()
"""

report = serialize.execSource(SCENE, "test/wait_for_video_scene.py")
assert report["ok"], report
said = subprocess.run(
    ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=nb_frames",
     "-of", "csv=p=0", "marius.mov"], capture_output=True, text=True, check=True).stdout.strip()
frames = int(said)
# The Text is line 7 of the scene; it is made of letters, each an element.
letters = [e for e in json.loads(report["scene"])["elements"] if e["line"] == 7]
assert letters, "no letter found on line 7"
begins = min(e["first"] for e in letters)
assert begins >= frames - 1, (begins, frames)
# `endFrame()` itself: a shape answers with its clock, a clip with its last image.
from videocode import Square, Video  # noqa: E402

shape = Square(side=1).opacity(0)
assert shape.endFrame() == shape.meta.lastAffectedFrame, shape.endFrame()
clip = Video("marius.mov", width=6).opacity(0)
assert clip.endFrame() >= frames - 1 > clip.meta.lastAffectedFrame, (clip.endFrame(), frames)

print("\033[32m\u2713\033[0m  waitFor(video) waits for the clip's last image, frame", begins, "of", frames)
