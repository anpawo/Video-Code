#!/usr/bin/env python3
"""
`waitFor(clip.end)` waits for the clip's last image; `waitFor(clip)` keeps
meaning its last effect, as for every other element.
"""
import json
import subprocess
import sys

sys.path.insert(0, ".")

import videocode.serialize as serialize  # noqa: E402
from videocode import Square, Video  # noqa: E402

SCENE = """from videocode import *
from videocode.template.effect.other.popIn import popIn

clip = Video("marius.mov", width=6).opacity(0)
clip.apply(popIn(duration=0.6))

merci = Text("Merci").opacity(0)
merci.waitFor(clip.end).fadeIn()
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

# `end` is the clip's own last image, in seconds of the film; a shape has none.
clip = Video("marius.mov", width=6).opacity(0)
assert abs(clip.end * 30 - frames) <= 1, (clip.end, frames)
assert not hasattr(Square(side=1), "end")
# `waitFor(seconds)` moves the clock to that second, never backwards.
late = Square(side=1).opacity(0).waitFor(2.0)
assert late.meta.lastAffectedFrame == 60, late.meta.lastAffectedFrame
assert late.waitFor(1.0).meta.lastAffectedFrame == 60

print("\033[32m\u2713\033[0m  waitFor(clip.end) waits for the clip's last image, frame", begins, "of", frames)
