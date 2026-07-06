#!/usr/bin/env python3

"""
Assertion-based tests for beat-sync (Tier 3: "audio onset detection ->
markers", `for beat in sound.beats(): logo.apply(pulse(start=beat))`).

Two parts:
  1. `_spectralFluxOnsets()` — the pure numpy spectral-flux/peak-picking
     math backing `Sound.beats()`, checked on synthetic sample arrays with
     known onset positions built directly in Python (no audio file, no
     `ffmpeg` involved).
  2. `Sound.beats()` end-to-end against a synthetic fixture WAV — a mono
     16-bit PCM file built with the stdlib `wave` module (no new
     dependency needed just for test-fixture generation, and no checked-in
     binary asset either) containing decaying-noise "click" bursts at
     known, evenly-spaced timestamps with silence in between — verifies
     real `ffmpeg`-decode + onset-detection agrees with the known
     ground-truth timestamps, and that no spurious onsets fire during the
     silent gaps.

Run directly: `python3 test/beat_sync_test.py`
"""

import atexit
import os
import random
import sys
import tempfile
import wave

sys.path.insert(0, ".")
sys.path.insert(0, "test")
from helpers import check, section, summary

from videocode import Sound
from videocode.input.media.Sound import _spectralFluxOnsets

import numpy as np


# ── _spectralFluxOnsets — pure math, synthetic sample arrays ───────────────
section("_spectralFluxOnsets — silence produces no onsets")

silence = np.zeros(8000, dtype=np.float32)
check("all-zero signal -> no onsets", _spectralFluxOnsets(silence, 8000, 1.5, 0.1) == [])

section("_spectralFluxOnsets — too-short signal returns empty, doesn't crash")

tiny = np.zeros(10, dtype=np.float32)
check("signal shorter than one window -> no onsets (no crash)", _spectralFluxOnsets(tiny, 8000, 1.5, 0.1) == [])


def burstSignal(sampleRate: int, durationSec: float, burstStartsSec: list[float], burstLen: int, seed: int) -> "np.ndarray":
    """Synthetic mono signal: silence except for short decaying-noise
    bursts starting at `burstStartsSec`, each `burstLen` samples long."""
    rng = random.Random(seed)
    nSamples = int(sampleRate * durationSec)
    signal = np.zeros(nSamples, dtype=np.float64)
    for t0 in burstStartsSec:
        start = int(t0 * sampleRate)
        for i in range(burstLen):
            if start + i >= nSamples:
                break
            env = np.exp(-i / (0.15 * burstLen))
            signal[start + i] += env * (rng.random() * 2 - 1) * 0.9
    return signal.astype(np.float32)


section("_spectralFluxOnsets — detects bursts at known sample positions")

SR1 = 8000
KNOWN1 = [0.2, 0.6, 1.0, 1.4]  # seconds, evenly spaced 0.4s apart
sig1 = burstSignal(SR1, 1.6, KNOWN1, burstLen=60, seed=1)
onsets1 = _spectralFluxOnsets(sig1, SR1, sensitivity=1.5, minInterval=0.1, windowSize=256, hopSize=128)

check(f"detected {len(onsets1)} onsets, expected {len(KNOWN1)}", len(onsets1) == len(KNOWN1))
if len(onsets1) == len(KNOWN1):
    errs = [abs(a - b) for a, b in zip(onsets1, KNOWN1)]
    print(f"    synthetic-array onset errors (s): {[round(e, 4) for e in errs]}")
    check("each detected onset within 30ms of its known burst", all(e < 0.03 for e in errs))

section("_spectralFluxOnsets — minInterval suppresses near-duplicate onsets")

# Two bursts only 20ms apart (well under a typical minInterval) should
# collapse to a single accepted onset.
closeBursts = burstSignal(SR1, 1.0, [0.4, 0.42], burstLen=40, seed=2)
onsetsClose = _spectralFluxOnsets(closeBursts, SR1, sensitivity=1.5, minInterval=0.2, windowSize=256, hopSize=128)
check("minInterval=0.2s collapses two 20ms-apart bursts into one onset", len(onsetsClose) == 1)


# ── Sound.beats() — real end-to-end verification against a synthetic WAV ───
section("Sound.beats() — real ffmpeg decode + detection matches synthetic ground truth")

SR2 = 44100
DURATION = 4.0
KNOWN2 = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5]  # 7 evenly-spaced beats, 0.5s apart
BURST_LEN = int(0.03 * SR2)  # 30ms decaying-noise burst

sig2 = burstSignal(SR2, DURATION, KNOWN2, burstLen=BURST_LEN, seed=42)
pcm16 = np.clip(sig2 * 32767, -32768, 32767).astype(np.int16)

FIXTURE = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
with wave.open(FIXTURE, "wb") as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(SR2)
    w.writeframes(pcm16.tobytes())
atexit.register(lambda: os.path.exists(FIXTURE) and os.remove(FIXTURE))

sound = Sound(FIXTURE)
detected = sound.beats()

check(f"detected {len(detected)} beats, expected {len(KNOWN2)}", len(detected) == len(KNOWN2))

if len(detected) == len(KNOWN2):
    errsMs = [(a - b) * 1000 for a, b in zip(detected, KNOWN2)]
    print(f"    detected:     {[round(t, 4) for t in detected]}")
    print(f"    ground truth: {KNOWN2}")
    print(f"    errors (ms):  {[round(e, 1) for e in errsMs]}")
    check("every detected beat within 50ms of its ground-truth timestamp", all(abs(e) < 50 for e in errsMs))
else:
    print(f"    detected:     {detected}")

section("Sound.beats() — no spurious onsets during silent gaps")

# Sample a handful of gap midpoints (between consecutive known beats, and
# before the first / after the last) and confirm no detected onset falls
# within 100ms of any of them.
gapMidpoints = [0.25] + [(a + b) / 2 for a, b in zip(KNOWN2, KNOWN2[1:])] + [3.75]
spurious = [g for g in gapMidpoints if any(abs(d - g) < 0.1 for d in detected)]
check("no detected onset near any silent-gap midpoint", spurious == [])

section("Sound.beats() — returns a plain sorted list[sec]")

check("result is sorted", detected == sorted(detected))
check("result is a list", isinstance(detected, list))

# ── summary ──────────────────────────────────────────────────────────────────
summary()
