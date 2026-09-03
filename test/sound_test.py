#!/usr/bin/env python3

"""
Assertion-based smoke tests for `Sound` (#78, "handle sound") —
verifies the Create-stack entry carries the args the C++ ffmpeg muxing
step (Compiler::generateVideo) needs: filepath, volume, delay, trimStart,
trimEnd.

Also pins down WHERE a sound plays: `start` is seconds after the script's
cursor, so a `Sound` written after a `wait()` plays where that line stands —
checked on the stack entry, on the timeline model the editor draws from, and
on a real render read back with ffmpeg's `silencedetect`.

Run directly: `python3 test/sound_test.py`
"""

import os
import subprocess
import sys
import tempfile

sys.path.insert(0, ".")
sys.path.insert(0, "test")
from helpers import check, needsRenderer, section, summary

from videocode import Sound, wait
from videocode.constants import FRAMERATE
from videocode.context import Context
from videocode.serialize import _resetContext, sceneModel

WAV = os.path.abspath("test/test.wav")


def delayOf(sound: Sound) -> float:
    return Context.stack[sound.meta.index][-1]["args"]["delay"]


section("Sound — Create-stack entry")
s = Sound("test/test.wav", start=1.5, volume=0.5, trimStart=0.5, trimEnd=1.5)
entry = Context.stack[s.meta.index][-1]
check("type is Sound", entry["type"] == "Sound")
check("filepath", entry["args"]["filepath"] == "test/test.wav")
check("volume", entry["args"]["volume"] == 0.5)
check("delay (start)", entry["args"]["delay"] == 1.5)
check("trimStart", entry["args"]["trimStart"] == 0.5)
check("trimEnd", entry["args"]["trimEnd"] == 1.5)

section("Sound — defaults")
s2 = Sound("test/test.wav")
entry2 = Context.stack[s2.meta.index][-1]
check("default volume", entry2["args"]["volume"] == 1.0)
check("default delay", entry2["args"]["delay"] == 0)
check("default trimStart", entry2["args"]["trimStart"] == 0)
check("default trimEnd is None", entry2["args"]["trimEnd"] is None)

# ── `start` is seconds after the cursor ──────────────────────────────────────
# The cursor only moves forward, and each scenario needs its own — hence the
# reset the editor already uses between two runs of a scene.
section("Sound — `start` is seconds after the cursor")

_resetContext()
wait(2)
check("wait(2), then no start at all → plays at 2.0s", delayOf(Sound(WAV)) == 2.0)

_resetContext()
wait(1)
check("wait(1), then start=0.5 → plays at 1.5s", delayOf(Sound(WAV, start=0.5)) == 1.5)

_resetContext()
check("no wait: start is the plain output delay it always was", delayOf(Sound(WAV, start=1.5)) == 1.5)

# `wait()` truncates its seconds into frames (`int(n * FRAMERATE)`), so the
# delay has to be read off the frame cursor, not off the seconds typed.
_resetContext()
wait(1.019)
check("delay follows the FRAME cursor, not the seconds asked for", delayOf(Sound(WAV)) == 30 / FRAMERATE)

section("Sound — the timeline bar and the mux agree")
_resetContext()
wait(2)
delayed = Sound(WAV)
delay = delayOf(delayed)
element = next(e for e in sceneModel()["elements"] if e["index"] == delayed.meta.index)
check("the bar the editor draws starts where ffmpeg plays it", element["first"] / FRAMERATE == delay)

# ── the rendered end ─────────────────────────────────────────────────────────
SCENE = f"""from videocode import *
wait(2)
Sound({WAV!r})
wait(2)
"""

OUTPUT_WIDTH = 160
OUTPUT_HEIGHT = 90


def renderScene(scenePath: str, outputPath: str) -> None:
    binary = os.path.abspath("video-code")
    if not os.path.exists(binary):
        raise FileNotFoundError(f"missing renderer binary: {binary}")

    subprocess.run(
        [binary, "--file", scenePath, "--generate", outputPath,
         "--width", str(OUTPUT_WIDTH), "--height", str(OUTPUT_HEIGHT),
         "--framerate", str(FRAMERATE)],
        check=True, capture_output=True, text=True,
    )


def firstSilenceEnd(videoPath: str) -> float | None:
    """
    Where the audio actually starts, in the rendered file. `test/test.wav` is
    2.00s with no silence in it, so the first `silence_end` IS the delay.
    """
    result = subprocess.run(
        ["ffmpeg", "-i", videoPath, "-af", "silencedetect=n=-40dB:d=0.1", "-f", "null", "-"],
        capture_output=True, text=True,
    )
    for line in result.stderr.splitlines():
        if "silence_end:" in line:
            return float(line.split("silence_end:")[1].split("|")[0])
    return None


section("Sound — rendered")
if not needsRenderer("a delayed sound has to be heard in an actual muxed file"):
    summary()
    sys.exit(0)

with tempfile.TemporaryDirectory() as tmp:
    scenePath = os.path.join(tmp, "scene.py")
    outputPath = os.path.join(tmp, "sound.mp4")
    with open(scenePath, "w", encoding="utf-8") as file:
        file.write(SCENE)

    try:
        renderScene(scenePath, outputPath)
        rendered = True
    except Exception as exc:
        check(f"render succeeded ({exc})", False)
        rendered = False

    if rendered:
        silenceEnd = firstSilenceEnd(outputPath)
        check("the render leads with silence, so the sound is not at t=0", silenceEnd is not None)
        check(
            f"the sound starts at the cursor, 2.0s (measured {silenceEnd})",
            silenceEnd is not None and abs(silenceEnd - 2.0) < 0.05,
        )

# ── summary ──────────────────────────────────────────────────────────────────
summary()
