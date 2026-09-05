#!/usr/bin/env python3

"""
Volume is a claim like any other — and the mux has to read it.

`music.over(duration=1.5).volume = 0` is the same sentence a shape answers to
when it fades, and it lands on the timeline as a per-frame claim in exactly the
same way. The renderer used to read only the constructor's `volume=`, so a fade
written that way came out at full level with nothing said about it.

The proof is a ratio, not a level: the same scene is rendered twice, once with
the claim and once without, and the two files are compared window by window.
That way nothing here depends on how loud the source file happens to be — only
on what the claim asked for.

Run directly: `python3 test/sound_claims_test.py`
"""

import math
import os
import subprocess
import sys
import tempfile
import wave

sys.path.insert(0, ".")
sys.path.insert(0, "test")
from helpers import check, needsTool, section, summary

from videocode import Sound
from videocode.context import Context
from videocode.serialize import _resetContext

WIDTH, HEIGHT = 160, 90
WINDOW = 0.1  # seconds per measured window

QUIET = """
from videocode import *

music = Sound("test/test.wav")
wait(2)
"""

RAMPED = """
from videocode import *

music = Sound("test/test.wav")
music.over(start=0.5, duration=0.3).volume = 0.2
wait(2)
"""

TOGETHER = """
from videocode import *

music = Sound("test/test.wav")
voice = Sound("test/test_speech.wav", start=0.3, trimEnd=0.8)
wait(4)
"""

DUCKED = """
from videocode import *

music = Sound("test/test.wav")
voice = Sound("test/test_speech.wav", start=0.3, trimEnd=0.8)
music.duck(under=voice, to=0.2, fade=0.15)
wait(4)
"""


def render(scene: str, output: str) -> None:
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as file:
        file.write(scene)
        path = file.name
    try:
        subprocess.run(
            [os.path.abspath("video-code"), "--file", path, "--generate", output,
             "--width", str(WIDTH), "--height", str(HEIGHT)],
            check=True, capture_output=True, text=True,
        )
    finally:
        os.unlink(path)


def envelope(path: str) -> list[float]:
    """The loudness of each window of the file's audio track, in order."""
    wav = path + ".wav"
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", path, "-ac", "1", "-ar", "16000", wav],
        check=True, capture_output=True, text=True,
    )
    with wave.open(wav) as track:
        rate = track.getframerate()
        raw = track.readframes(track.getnframes())

    step = int(rate * WINDOW) * 2  # 16-bit samples
    out = []
    for at in range(0, len(raw) - step, step):
        block = raw[at:at + step]
        total = 0
        for i in range(0, len(block), 2):
            sample = int.from_bytes(block[i:i + 2], "little", signed=True)
            total += sample * sample
        out.append(math.sqrt(total / (len(block) // 2)))
    return out


# ── What the two new verbs put on the timeline ─────────────────────────────
# Read off the stack rather than out of a render: this is the half that is
# arithmetic, and it is worth failing on its own so a broken duck is not
# reported as a broken mux.
section("what duck() writes, and what a sound says its length is")
_resetContext()

whole = Sound("test/test.wav")
check(f"a sound is as long as its file ({whole.length():.2f}s of 2.00)", abs(whole.length() - 2.0) < 0.02)
trimmed = Sound("test/test.wav", trimStart=0.5, trimEnd=1.5)
check(f"trimmed, it is as long as the part that plays ({trimmed.length():.2f}s)", abs(trimmed.length() - 1.0) < 0.02)
check("a file that is not there is not a length", Sound("test/nothing-here.wav").length() == 0.0)

_resetContext()
music = Sound("test/test.wav")
voice = Sound("test/test_speech.wav", start=0.3, trimEnd=0.8)
music.duck(under=voice, to=0.2, fade=0.15)

entry = Context.stack[music.meta.index]
claimed = [(frame, round(entry[frame][key]["args"]["value"], 3))
           for frame in sorted(f for f in entry if f != -1)
           for key in entry[frame] if key.startswith("Args")]
low = min(range(len(claimed)), key=lambda i: claimed[i][1])
check(f"duck writes two ramps, one down and one up ({len(claimed)} frames claimed)",
      len(claimed) >= 4 and 0 < low < len(claimed) - 1
      and all(claimed[i][1] >= claimed[i + 1][1] for i in range(low))
      and all(claimed[i][1] <= claimed[i + 1][1] for i in range(low, len(claimed) - 1)))
check("it goes down before the voice starts", claimed[0][0] < 0.3 * 30 and claimed[0][1] < 1.0)
check(f"as far as `to` ({min(v for _, v in claimed)})", abs(min(v for _, v in claimed) - 0.2) < 0.001)
check("and comes back to where it was", abs(claimed[-1][1] - 1.0) < 0.001)
check(f"once the voice is over, its own length included (frame {claimed[-1][0]} of 33+)",
      claimed[-1][0] >= (voice.delay + voice.length()) * 30)

_resetContext()

if not needsTool("./video-code", "rendering needs the built binary"):
    summary()
    sys.exit(0)
if not needsTool("ffmpeg", "reading the track back needs ffmpeg"):
    summary()
    sys.exit(0)

with tempfile.TemporaryDirectory() as tmp:
    # ── A ramp written as a claim ──────────────────────────────────────────
    section("a volume written with over() reaches the file")
    plain = os.path.join(tmp, "plain.mp4")
    ramped = os.path.join(tmp, "ramped.mp4")
    render(QUIET, plain)
    render(RAMPED, ramped)

    before, after = envelope(plain), envelope(ramped)
    check(f"both renders hold the same stretch of audio ({len(before)} windows)",
          abs(len(before) - len(after)) <= 1 and len(before) >= 15)

    def ratio(first: float, last: float) -> float:
        """How much quieter the claimed render is, over the seconds [first, last)."""
        top = sum(before[int(first / WINDOW):int(last / WINDOW)])
        low = sum(after[int(first / WINDOW):int(last / WINDOW)])
        return low / top if top > 0 else 0.0

    head = ratio(0.0, 0.5)
    tail = ratio(1.0, 1.9)
    check(f"before the ramp the two files are the same sound (ratio {head:.2f})", 0.9 < head < 1.1)
    check(f"after it the claimed one is a fifth as loud (ratio {tail:.2f})", 0.13 < tail < 0.30)
    middle = ratio(0.5, 0.8)
    check(f"and the ramp itself is between the two (ratio {middle:.2f})", tail < middle < head)

    # ── The move that made volume worth claiming ───────────────────────────
    section("duck() lowers the music under the voice, and lets it back")
    # Against the same two sounds WITHOUT the duck, for the same reason as
    # above: what is being measured is the claim, not the recording.
    mixed = os.path.join(tmp, "mixed.mp4")
    ducked = os.path.join(tmp, "ducked.mp4")
    render(TOGETHER, mixed)
    render(DUCKED, ducked)
    before, after = envelope(mixed), envelope(ducked)

    # The voice runs 0.3 s → 0.8 s (its `trimEnd` is what `length()` reads), and
    # the music runs 0 → 2 s. So there is music alone before it, the two of them
    # over it, and music alone again after — which is the whole shape `duck`
    # writes, measured in one file.
    check(f"before the voice, nothing is touched (ratio {ratio(0.0, 0.1):.2f})", 0.9 < ratio(0.0, 0.1) < 1.1)
    check(f"under the voice the mix is lower (ratio {ratio(0.35, 0.75):.2f})", ratio(0.35, 0.75) < 0.92)
    # Measured once the way back is finished — the ramp is 0.15 s from 1.1 s,
    # and averaging over it would only measure the ramp.
    check(f"and the music is itself again after it (ratio {ratio(1.5, 1.9):.2f})", 0.9 < ratio(1.5, 1.9) < 1.1)

summary()
