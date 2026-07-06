#!/usr/bin/env python3

"""
Assertion-based tests for auto-captions (Tier 3, last backlog item: "whisper
-> existing subtitle system", `Subtitles(sound.transcribe())`).

Three parts:
  1. `_secondsToSrtTimestamp()`/`_segmentsToSrt()` — the pure SRT-formatting
     helpers backing `Sound.transcribe()`, checked on known (start, end,
     text) tuples with no whisper model involved, and round-tripped through
     the EXISTING `_SubtitleHelper.parseSRT()` (imported, not modified) to
     prove the generated text is valid, parseable SRT.
  2. `Sound.transcribe()` end-to-end against a real, short, spoken-word
     fixture clip — `test/test_speech.wav`, a 16kHz mono WAV generated once
     via macOS `say -o ... "the quick brown fox jumps over the lazy dog"`
     then downsampled with `ffmpeg` and checked in (mirrors `test/test.wav`'s
     existing precedent of a small committed binary audio fixture; unlike
     `beat_sync_test.py`'s synthetic-noise-burst WAV, real speech can't be
     synthesized on the fly without a TTS dependency, so this one fixture is
     checked in instead, keeping the test itself portable/deterministic
     across platforms — no `say`/TTS call at test-run time). Runs the real
     `faster-whisper` "tiny" model (downloaded once, then cached), asserts
     the generated `.srt` parses via the real `parseSRT()` and that its text
     recognizably contains the known spoken phrase.
  3. `Subtitles(sound.transcribe())` — builds a real `Subtitles` group from
     the generated `.srt` and confirms it produces the expected `Text`
     children.

Run directly: `python3 test/transcribe_test.py`

Note: this test downloads the "tiny" whisper model on first run (~75MB,
cached afterward by `faster-whisper`/`huggingface_hub`) and runs real CPU
inference — slower than most other test/*_test.py files, but kept as small
as reasonably possible (tiny model, ~2.4s fixture clip) so `./test/run_tests.sh`
stays practical to run repeatedly.
"""

import re
import sys

sys.path.insert(0, ".")
sys.path.insert(0, "test")
from helpers import check, section, summary

from videocode import Sound, Subtitles
from videocode.input.media.Sound import _secondsToSrtTimestamp, _segmentsToSrt
from videocode.input.shape.text._SubtitleHelper import parseSRT

FIXTURE = "test/test_speech.wav"
SPOKEN_PHRASE = "the quick brown fox jumps over the lazy dog"


# ── _secondsToSrtTimestamp ──────────────────────────────────────────────────
section("_secondsToSrtTimestamp — formats seconds as HH:MM:SS,mmm")

check("zero", _secondsToSrtTimestamp(0) == "00:00:00,000")
check("sub-second", _secondsToSrtTimestamp(1.234) == "00:00:01,234")
check("minutes+seconds", _secondsToSrtTimestamp(75.5) == "00:01:15,500")
check("hours", _secondsToSrtTimestamp(3661.001) == "01:01:01,001")


# ── _segmentsToSrt ───────────────────────────────────────────────────────────
section("_segmentsToSrt — renders (start, end, text) tuples as valid SRT text")

srt = _segmentsToSrt([(1.0, 3.0, "Hello, world!"), (4.5, 7.25, "This is a subtitle")])
check("starts with sequential index 1", srt.startswith("1\n"))
check("contains second index", "\n2\n" in srt)
check("contains first timing line", "00:00:01,000 --> 00:00:03,000" in srt)
check("contains second timing line", "00:00:04,500 --> 00:00:07,250" in srt)

blankOnly = _segmentsToSrt([(0.0, 1.0, "   ")])
check("blank-text segments are dropped", blankOnly == "")

section("_segmentsToSrt — round-trips through the EXISTING parseSRT()")

import tempfile, os

roundTripPath = tempfile.NamedTemporaryFile(suffix=".srt", delete=False).name
with open(roundTripPath, "w", encoding="utf-8") as f:
    f.write(srt)
cues = parseSRT(roundTripPath)
os.remove(roundTripPath)

check("two cues parsed back", len(cues) == 2)
check("first cue timing round-trips", cues[0].start == 1.0 and cues[0].end == 3.0)
check("first cue text round-trips", cues[0].text == "Hello, world!")
check("second cue text round-trips", cues[1].text == "This is a subtitle")


# ── Sound.transcribe() — real whisper model against a real spoken clip ─────
section("Sound.transcribe() — real faster-whisper transcription of a real spoken clip")

sound = Sound(FIXTURE)
srtPath = sound.transcribe(model="tiny", language="en")

check("returns a path to a file that exists", os.path.isfile(srtPath))

transcribedCues = parseSRT(srtPath)
check("produces at least one cue", len(transcribedCues) >= 1)

fullText = " ".join(cue.text for cue in transcribedCues)
print(f"    ground truth: {SPOKEN_PHRASE!r}")
print(f"    transcribed:  {fullText!r}")


def normalize(s: str) -> list[str]:
    return re.sub(r"[^a-z0-9\s]", "", s.lower()).split()


expectedWords = normalize(SPOKEN_PHRASE)
gotWords = normalize(fullText)
matched = sum(1 for w in expectedWords if w in gotWords)
check(
    f"transcribed text recognizably contains the spoken phrase "
    f"({matched}/{len(expectedWords)} words matched)",
    matched >= len(expectedWords) - 1,  # tolerate at most one dropped/mis-heard word
)

os.remove(srtPath)

section("Sound.transcribe() — outputPath is honored when given")

explicitPath = tempfile.NamedTemporaryFile(suffix=".srt", delete=False).name
os.remove(explicitPath)  # transcribe() should create it
returned = sound.transcribe(outputPath=explicitPath, model="tiny", language="en")
check("returns the given outputPath", returned == explicitPath)
check("file was written at outputPath", os.path.isfile(explicitPath))


# ── Subtitles(sound.transcribe()) — full integration ────────────────────────
section("Subtitles(sound.transcribe()) — builds real Text children from a real transcript")

sub = Subtitles(explicitPath)
check("at least one Text child", len(sub.inputs) >= 1)
check("all start hidden", all(t.meta.hidden for t in sub.inputs))

os.remove(explicitPath)

# ── summary ──────────────────────────────────────────────────────────────────
summary()
