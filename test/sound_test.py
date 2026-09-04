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

And that `--from` / `--to` keep it there: a stretch rendered on its own has
the frames of that stretch and the sound at the moment it had in the whole.

Run directly: `python3 test/sound_test.py`
"""

import os
import subprocess
import sys
import tempfile

sys.path.insert(0, ".")
sys.path.insert(0, "test")
from helpers import check, needsRenderer, needsTool, section, summary

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
timestamp("cue")
Sound({WAV!r})
wait(2)
"""

OUTPUT_WIDTH = 160
OUTPUT_HEIGHT = 90


def renderScene(scenePath: str, outputPath: str, *flags: str) -> None:
    binary = os.path.abspath("video-code")
    if not os.path.exists(binary):
        raise FileNotFoundError(f"missing renderer binary: {binary}")

    subprocess.run(
        [binary, "--file", scenePath, "--generate", outputPath,
         "--width", str(OUTPUT_WIDTH), "--height", str(OUTPUT_HEIGHT),
         "--framerate", str(FRAMERATE), *flags],
        check=True, capture_output=True, text=True,
    )


def videoFrames(videoPath: str) -> int:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_frames", "-show_entries", "stream=nb_read_frames", "-of", "csv=p=0", videoPath],
        capture_output=True, text=True,
    )
    return int(result.stdout)


def audioDuration(videoPath: str) -> float | None:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=duration", "-of", "csv=p=0", videoPath],
        capture_output=True, text=True,
    )
    return float(result.stdout) if result.stdout.strip() else None


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

# ── a stretch of the scene ───────────────────────────────────────────────────
# The same 4 s scene, sound at 2 s. A range is frames [from, to) of the whole,
# and the sound has to sit where the whole had it: at 1.0 s of a render that
# starts at 1 s, at 0 of one that starts after it began — cut, not moved.
section("--from / --to — the picture is the stretch, the sound stays where it was")
if needsRenderer("a stretch has to be rendered to be counted") and needsTool("ffprobe", "counting the frames back"):
    with tempfile.TemporaryDirectory() as tmp:
        scenePath = os.path.join(tmp, "scene.py")
        with open(scenePath, "w", encoding="utf-8") as file:
            file.write(SCENE)

        def stretch(name: str, *flags: str) -> str:
            outputPath = os.path.join(tmp, f"{name}.mp4")
            renderScene(scenePath, outputPath, *flags)
            return outputPath

        try:
            whole = stretch("whole")
            check(f"the whole scene is 120 frames (measured {videoFrames(whole)})", videoFrames(whole) == 120)

            before = stretch("before", "--from", "1", "--to", "3")
            check(f"--from 1 --to 3 renders 60 frames (measured {videoFrames(before)})", videoFrames(before) == 60)
            silenceEnd = firstSilenceEnd(before)
            check(f"and the sound, at 2 s of the scene, is at 1.0 s of the stretch (measured {silenceEnd})", silenceEnd is not None and abs(silenceEnd - 1.0) < 0.05)

            after = stretch("after", "--from", "3")
            check(f"--from 3 renders the last 30 frames (measured {videoFrames(after)})", videoFrames(after) == 30)
            check("the sound began 1 s before the stretch, so it is playing at 0 — no silence to detect", firstSilenceEnd(after) is None)
            duration = audioDuration(after)
            check(f"and only its second half is heard: 1.0 s of audio (measured {duration})", duration is not None and abs(duration - 1.0) < 0.05)

            clamped = stretch("clamped", "--from", "0", "--to", "99")
            check(f"--to past the end is clamped, not refused: 120 frames (measured {videoFrames(clamped)})", videoFrames(clamped) == 120)

            named = stretch("named", "--from", "cue", "--to", "3")
            check(f"--from takes a timestamp() name: 'cue' is 2 s, so 30 frames (measured {videoFrames(named)})", videoFrames(named) == 30)
            check("and the sound, written right after the cue, starts at 0", firstSilenceEnd(named) is None)
        except subprocess.CalledProcessError as exc:
            check(f"render succeeded ({exc.stderr.strip()})", False)

# ── a Video's own sound ──────────────────────────────────────────────────────
# The picture's clock starts at output frame 0 and skips the cut ranges, so the
# sound has to start at 0 and skip the same ranges. The fixture makes a cut
# audible: silent for its first second, a tone for its second — a head cut
# that reaches the audio removes the silence, one that does not leaves it.
section("Video — its own sound reaches the mux, cut like the picture")


def toneClip(path: str, fps: int) -> None:
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error",
         "-f", "lavfi", "-i", f"color=c=blue:s=320x180:d=2:r={fps}",
         "-f", "lavfi", "-i", "aevalsrc=if(gte(t\\,1)\\,0.5*sin(440*2*PI*t)):s=48000:d=2",
         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", path],
        check=True,
    )


def renderVideoScene(tmp: str, name: str, line: str) -> str:
    scenePath = os.path.join(tmp, f"{name}.py")
    outputPath = os.path.join(tmp, f"{name}.mp4")
    with open(scenePath, "w", encoding="utf-8") as file:
        file.write(f"from videocode import *\n{line}\nwait(3)\n")
    renderScene(scenePath, outputPath)
    return outputPath


if needsRenderer("a video's sound has to be heard in an actual muxed file") and needsTool("ffprobe", "reading the muxed streams back"):
    with tempfile.TemporaryDirectory() as tmp:
        clip30 = os.path.join(tmp, "tone30.mp4")
        toneClip(clip30, fps=30)

        whole = renderVideoScene(tmp, "whole", f"Video({clip30!r})")
        check("the render carries an audio stream", audioDuration(whole) is not None)
        silenceEnd = firstSilenceEnd(whole)
        check(f"the tone sits where the file has it, 1.0s (measured {silenceEnd})", silenceEnd is not None and abs(silenceEnd - 1.0) < 0.05)

        head = renderVideoScene(tmp, "head", f"Video({clip30!r}, startFrame=30)")
        duration = audioDuration(head)
        check(f"startFrame=30 drops the silent second: 1.0s of audio left (measured {duration})", duration is not None and abs(duration - 1.0) < 0.05)
        check("and the tone starts at 0, so there is no silence to detect", firstSilenceEnd(head) is None)

        middle = renderVideoScene(tmp, "middle", f"Video({clip30!r}, cuts=[(15, 45)])")
        silenceEnd = firstSilenceEnd(middle)
        check(f"cuts=[(15, 45)] joins 0.5s of silence to 0.5s of tone (measured {silenceEnd})", silenceEnd is not None and abs(silenceEnd - 0.5) < 0.05)

        # One source frame per scene frame: a 60 fps clip plays at half speed,
        # and its sound has to take the same 4 seconds.
        clip60 = os.path.join(tmp, "tone60.mp4")
        toneClip(clip60, fps=60)
        slow = renderVideoScene(tmp, "slow", f"Video({clip60!r})")
        silenceEnd = firstSilenceEnd(slow)
        check(f"a 60 fps source is retimed with its picture: tone at 2.0s (measured {silenceEnd})", silenceEnd is not None and abs(silenceEnd - 2.0) < 0.1)

# ── summary ──────────────────────────────────────────────────────────────────
summary()
