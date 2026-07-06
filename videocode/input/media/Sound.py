#!/usr/bin/env python3

from __future__ import annotations

import subprocess
import tempfile
from typing import TYPE_CHECKING

from videocode.input.input import Input
from videocode.utils.decorators import inputCreation
from videocode.ty import *

if TYPE_CHECKING:
    import numpy as np


__all__ = ["Sound"]


def _spectralFluxOnsets(
    samples: "np.ndarray",
    sampleRate: int,
    sensitivity: number,
    minInterval: sec,
    windowSize: int = 1024,
    hopSize: int = 512,
    smoothing: int = 15,
) -> list[sec]:
    """
    Pure numpy onset-detection math backing `Sound.beats()` — factored out
    so it's testable on synthetic sample arrays without decoding any actual
    audio file. See `Sound.beats()`'s docstring for the full algorithm
    description; in short: framed spectral flux (half-wave-rectified
    frame-to-frame magnitude-spectrum increase) as an "onset strength"
    signal, peak-picked against a local moving-average threshold scaled by
    `sensitivity`, with a `minInterval`-seconds minimum spacing between
    accepted onsets.

    `samples` is a 1D mono `float32`/`float64` array; `sampleRate` is its
    sample rate in Hz. `windowSize`/`hopSize` are in samples; `smoothing` is
    the half-width (in frames) of the moving-average threshold window on
    each side (so the window spans `2 * smoothing + 1` frames).
    """
    import numpy as np

    if len(samples) < windowSize:
        return []

    window = np.hanning(windowSize)
    nFrames = 1 + (len(samples) - windowSize) // hopSize
    if nFrames < 2:
        return []

    # One magnitude spectrum per frame.
    magnitudes = np.empty((nFrames, windowSize // 2 + 1), dtype=np.float64)
    for i in range(nFrames):
        start = i * hopSize
        frame = samples[start:start + windowSize] * window
        magnitudes[i] = np.abs(np.fft.rfft(frame))

    # Spectral flux: half-wave-rectified frame-to-frame magnitude increase,
    # summed across bins. `flux[0]` has no predecessor, so it's left at 0.
    flux = np.zeros(nFrames, dtype=np.float64)
    diff = magnitudes[1:] - magnitudes[:-1]
    flux[1:] = np.sum(np.maximum(0.0, diff), axis=1)

    # Local adaptive threshold: a centered moving average of the flux signal
    # over a `2 * smoothing + 1`-frame window, scaled by `sensitivity` — a
    # frame must exceed its own local baseline (not a fixed global one) to
    # count as a candidate onset, so the detector adapts to quiet vs. loud
    # sections of the track instead of using one threshold for the whole file.
    threshold = np.empty(nFrames, dtype=np.float64)
    for i in range(nFrames):
        lo = max(0, i - smoothing)
        hi = min(nFrames, i + smoothing + 1)
        threshold[i] = sensitivity * float(np.mean(flux[lo:hi]))

    minIntervalFrames = max(1, int(round(minInterval * sampleRate / hopSize)))

    onsets: list[sec] = []
    lastAcceptedFrame = -minIntervalFrames
    for i in range(1, nFrames - 1):
        if flux[i] <= threshold[i]:
            continue
        # local maximum check
        if flux[i] < flux[i - 1] or flux[i] < flux[i + 1]:
            continue
        if i - lastAcceptedFrame < minIntervalFrames:
            continue
        onsets.append(i * hopSize / sampleRate)
        lastAcceptedFrame = i

    return onsets


def _secondsToSrtTimestamp(t: sec) -> str:
    """Format a seconds value as an SRT timestamp (`HH:MM:SS,mmm`)."""
    totalMillis = round(t * 1000)
    hours, rem = divmod(totalMillis, 3600_000)
    minutes, rem = divmod(rem, 60_000)
    seconds, millis = divmod(rem, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"


def _segmentsToSrt(segments: list[tuple[sec, sec, str]]) -> str:
    """
    Render `(start, end, text)` segments (seconds) into `.srt`-format text —
    factored out from `Sound.transcribe()` so it's testable without running
    any actual whisper model. Blank-text segments (whisper occasionally
    emits these for pure-silence/noise stretches) are dropped. Blocks are
    separated by a blank line and prefixed with sequential 1-based index
    lines, matching conventional `.srt` output (`_SubtitleHelper.parseSRT`
    itself doesn't require the index line, but other tooling may expect it).
    """
    blocks: list[str] = []
    for i, (start, end, text) in enumerate(segments, start=1):
        text = text.strip()
        if not text:
            continue
        blocks.append(f"{i}\n{_secondsToSrtTimestamp(start)} --> {_secondsToSrtTimestamp(end)}\n{text}")

    return "\n\n".join(blocks) + ("\n" if blocks else "")


class Sound(Input):
    """
    A purely auditory input — adds an audio track to the output video.

    `start` is when the track begins playing in the output timeline (seconds).
    `trimStart`/`trimEnd` cut the source file's own audio to `[trimStart, trimEnd)`
    (seconds, `trimEnd=None` plays to the end of the source).
    `volume` is a linear multiplier (1.0 = unchanged).

    Multiple `Sound` inputs are mixed together in the output.
    """

    cppName = "Sound"
    cppAttrs = {"filepath", "volume", "delay", "trimStart", "trimEnd"}

    @property
    def width(self) -> wnumber:
        return 0

    @property
    def height(self) -> wnumber:
        return 0

    @inputCreation
    def __init__(
        self,
        filepath: str,
        start: sec = 0,
        volume: ufloat = 1.0,
        trimStart: sec = 0,
        trimEnd: maybe[sec] = None,
    ) -> None:
        self.filepath = filepath
        self.delay = start
        self.volume = volume
        self.trimStart = trimStart
        self.trimEnd = trimEnd

    def beats(
        self,
        sensitivity: number = 1.5,
        minInterval: sec = 0.1,
    ) -> list[sec]:
        """
        Detect onset/transient timestamps in this `Sound`'s source audio —
        good enough for `pulse()`-style effect markers:

            for beat in sound.beats():
                logo.apply(pulse(start=beat))

        Algorithm — spectral flux onset detection with adaptive-threshold
        peak-picking, a simple, well-known, dependency-free technique (no
        `librosa`/`aubio` needed, just `numpy`):

        1. The source file is decoded to mono PCM via `ffmpeg` (not
           `ffprobe` — this one reads actual sample data, not metadata),
           resampled to a fixed 22050 Hz analysis rate (plenty for onset
           detection, keeps the FFT cheap).
        2. The signal is split into overlapping 1024-sample windows (512-
           sample hop) with a Hann taper, and each window's magnitude
           spectrum is computed via `np.fft.rfft`.
        3. "Spectral flux" per frame = the half-wave-rectified sum of
           frame-to-frame magnitude increases (`sum(max(0, mag[i] -
           mag[i-1]))`) — a 1D onset-strength signal over time that spikes
           on sharp spectral changes (drum hits, sharp attacks, clicks).
        4. A frame is accepted as an onset if its flux exceeds
           `sensitivity` times the local moving-average flux (adapts to
           quiet vs. loud sections instead of one fixed global threshold),
           is a local maximum, and is at least `minInterval` seconds past
           the previously accepted onset (suppresses clusters of near-
           duplicate hits from a single transient).
        5. Accepted frame indices are converted to second-timestamps and
           returned sorted.

        `sensitivity` — multiplier on the local average flux a frame must
        exceed to count as an onset. Higher = fewer, more confident onsets;
        lower = more onsets, including softer ones.

        `minInterval` — minimum spacing (seconds) enforced between two
        accepted onsets.

        Known limitations — this is **onset/transient detection, not a true
        music beat-tracker**: unlike `aubio`/`librosa`'s beat trackers,
        there is no BPM estimation and no downbeat/meter awareness. It fires
        on any sufficiently sharp spectral change, which is often exactly
        what "beat" markers want for `pulse()`-style effects (drum hits,
        clicks, sharp attacks), but it will NOT track a sustained/legato
        musical beat that has no transient attacks (e.g. a slow string
        swell with no percussive onset).

        Requires `numpy` (see `requirements.txt`) and an `ffmpeg` binary on
        `PATH` — imported/invoked lazily here, mirroring `Video.track()`'s
        lazy-`cv2` convention, so scripts that never call `.beats()` don't
        need either installed.
        """
        try:
            import numpy as np
        except ImportError as e:
            raise ImportError(
                "Sound.beats() needs numpy — install it with `pip install numpy` "
                "(this is intentionally not a hard dependency of videocode: only "
                ".beats() callers need it)."
            ) from e

        analysisRate = 22050
        result = subprocess.run(
            ["ffmpeg", "-v", "error", "-i", self.filepath,
             "-f", "f32le", "-ac", "1", "-ar", str(analysisRate), "-"],
            capture_output=True, check=True,
        )
        samples = np.frombuffer(result.stdout, dtype=np.float32)

        return _spectralFluxOnsets(samples, analysisRate, sensitivity, minInterval)

    def transcribe(
        self,
        outputPath: maybe[str] = None,
        model: str = "tiny",
        language: maybe[str] = None,
    ) -> str:
        """
        Transcribe this `Sound`'s source audio to speech-to-text captions and
        write them out as a real `.srt` file — feeds directly into the
        existing subtitle system with zero changes needed there:

            subs = Subtitles(sound.transcribe())

        Algorithm — runs OpenAI's Whisper speech-recognition model via
        `faster-whisper` (a CTranslate2-based re-implementation of the same
        published Whisper weights; no PyTorch dependency, much smaller
        install, faster CPU inference than the reference `openai-whisper`
        package). `faster-whisper` decodes `self.filepath` itself (via
        bundled `PyAV`/ffmpeg libs — confirmed working directly against both
        `.wav` and `.aiff` in testing, no manual pre-conversion needed) and
        returns a stream of timed segments (`start`/`end` in seconds, plus
        the recognized `text`), which are converted here into conventional
        `.srt` text (`HH:MM:SS,mmm --> HH:MM:SS,mmm` timing lines, sequential
        1-based index lines, blank line between blocks — see
        `_segmentsToSrt()`) and written to `outputPath`.

        `outputPath` — where to write the `.srt` file; if omitted, a new
        temp file is created (`tempfile.NamedTemporaryFile(suffix=".srt",
        delete=False)`) and its path returned. Either way, the path is
        returned so `Subtitles(sound.transcribe())` works directly.

        `model` — the Whisper model size/name (`"tiny"`, `"base"`, `"small"`,
        `"medium"`, `"large-v3"`, or a `"<size>.en"` English-only variant).
        Defaults to `"tiny"`: smallest download (~75MB) and fastest CPU
        inference, at the cost of accuracy — fine for rough/preview captions;
        pass a larger model (e.g. `"small"` or `"medium"`) for meaningfully
        better transcription quality on real projects. Model weights are
        downloaded from Hugging Face on first use and cached locally by
        `faster-whisper`/`huggingface_hub`, so the first call for a given
        model name is slow (network + disk) and subsequent calls are fast.

        `language` — optional ISO-639-1 code (e.g. `"en"`, `"fr"`) hinting
        the source language; if `None`, Whisper auto-detects it from the
        first ~30s of audio. Auto-detection is a reasonable default but can
        misfire on short, noisy, or accented clips — pass an explicit code
        if you know it.

        Known limitations — the `tiny` default trades accuracy for speed:
        expect occasional dropped/mis-heard words, especially on fast
        speech, background noise, or uncommon vocabulary/names; it is NOT a
        verbatim-perfect transcript. Segment boundaries are Whisper's own
        (voice-activity-based) sentence/phrase splits, not guaranteed to
        align with natural subtitle line lengths — long segments may render
        as a single long `Text` line via `Subtitles`. This runs the model
        synchronously on CPU; there is no GPU acceleration path wired up
        here (`faster-whisper` supports CUDA, but that's a separate install
        or configuration this method doesn't attempt).

        Requires `faster-whisper` (see `requirements.txt`) — imported lazily
        here, mirroring `Sound.beats()`'s lazy-`numpy` convention, so scripts
        that never call `.transcribe()` don't need it installed.
        """
        try:
            from faster_whisper import WhisperModel
        except ImportError as e:
            raise ImportError(
                "Sound.transcribe() needs faster-whisper — install it with "
                "`pip install faster-whisper` (this is intentionally not a hard "
                "dependency of videocode: only .transcribe() callers need it)."
            ) from e

        whisperModel = WhisperModel(model, device="cpu", compute_type="int8")
        segments, _info = whisperModel.transcribe(self.filepath, language=language)

        srtText = _segmentsToSrt([(seg.start, seg.end, seg.text) for seg in segments])

        if outputPath is None:
            outputPath = tempfile.NamedTemporaryFile(suffix=".srt", delete=False).name

        with open(outputPath, "w", encoding="utf-8") as file:
            file.write(srtText)

        return outputPath
