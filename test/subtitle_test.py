#!/usr/bin/env python3

"""
Assertion-based smoke tests for `Subtitles` (#79, "handle subtitles") —
verifies `.srt` parsing and that each cue line becomes a hidden `Text`
shown/hidden at the right timestamps.
Run directly: `python3 test/subtitle_test.py`
"""

import sys

sys.path.insert(0, ".")
sys.path.insert(0, "test")
from helpers import check, section, summary

from videocode import Subtitles
from videocode.input.shape.text._SubtitleHelper import parseSRT

# ── parseSRT ─────────────────────────────────────────────────────────────────
section("parseSRT — reads cues with timestamps and text")
cues = parseSRT("test/test.srt")
check("two cues", len(cues) == 2)
check("first cue timing", cues[0].start == 1.0 and cues[0].end == 3.0)
check("first cue text", cues[0].text == "Hello, world!")
check("second cue timing", cues[1].start == 4.5 and cues[1].end == 7.25)
check("second cue multi-line text", cues[1].text == "This is a subtitle\nwith two lines")

# ── Subtitles ────────────────────────────────────────────────────────────────
section("Subtitles — one Text per cue line, hidden outside its timing window")
sub = Subtitles("test/test.srt")
check("one Text per line (1 + 2)", len(sub.inputs) == 3)
check("all start hidden", all(t.meta.hidden for t in sub.inputs))

ys = [t.meta.position.y for t in sub.inputs]
check("multi-line cue stacks vertically", ys[1] != ys[2])
check("single-line cue shares the base y with the last line of cue 2", ys[0] == ys[2])

# ── summary ──────────────────────────────────────────────────────────────────
summary()
