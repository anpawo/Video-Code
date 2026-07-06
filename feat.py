#!/usr/bin/env python3

# feat.py — full recap reel of every editor-parity feature (Tier 1 + 2 + 3),
# one short, self-contained section per feature, played strictly in sequence.
# One-off recap at the user's request — the usual "newest batch only"
# convention resumes with the next batch.
#
# Tier 1 — compositing        Tier 2 — engine              Tier 3 — code-first
#  1. Blend modes              5. Track mattes              10. Motion tracking
#  2. Chroma key               6. LUT color grade           11. Beat-sync
#  3. Glow                     7. Adjustment layers         12. Auto-captions
#  4. Transitions              8. Video time remapping
#                              9. Alpha + GIF export
#
# Every media-based demo uses REAL generated assets (cv2-encoded clips with
# burned-in frame counters, a stdlib-wave click track, the checked-in speech
# fixture) — really decoded, tracked, analyzed and transcribed at build time.
#
# Preview: ./video-code --file feat.py

import random
import struct
import tempfile
import wave

import cv2
import numpy as np

from videocode import *
from videocode.template.effect.other.pulse import pulse
from videocode.template.effect.other.transitions import crossfade, push
from videocode.template.input.CompoundPolygon import CompoundPolygon

HOLD = 1.6
FADE = 0.4


def section(name: str, caption: str, *items: Input) -> Group:
    """Title (the API call) + plain-words caption + this section's items."""
    title = Text(name, fontSize=0.32, fillColor=WHITE).position(0, 3.7)
    sub = Text(caption, fontSize=0.16, fillColor=WHITE | 0.65).position(0, 3.15)
    g = Group(title, sub, *items)
    g.fadeIn(duration=FADE)
    return g


def close(g: Group, hold: sec = HOLD) -> None:
    """Hold, then fade the whole section out before the next one starts."""
    g.waitForOthers().wait(hold).fadeOut(duration=FADE, hide=True)
    # `g.wait()` above only advances this group's OWN local schedule. The
    # module-level `wait()` (no target) is the actual global clock: it syncs
    # to the true end of everything scheduled so far, so the NEXT section's
    # brand-new inputs start right here instead of all defaulting to frame 0.
    wait()


def clip(nLead: int, nActive: int, w: int, h: int, draw) -> str:
    """
    Encode a real mp4 whose first `nLead` frames repeat active-frame 0.
    Videos play against the GLOBAL frame index, so a clip meant for a
    section starting at global frame S needs S lead-in frames baked in.
    """
    path = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False).name
    writer = cv2.VideoWriter(path, cv2.VideoWriter.fourcc(*"mp4v"), FRAMERATE, (w, h))
    for f in range(nLead + nActive):
        img = np.zeros((h, w, 3), dtype=np.uint8)
        draw(img, max(0, f - nLead))
        writer.write(img)
    writer.release()
    return path


def label(text: str, x: wnumber, y: wnumber) -> Text:
    return Text(text, fontSize=0.16, fillColor=WHITE | 0.6).position(x, y)


# ── 1. Blend modes ───────────────────────────────────────────────────────────
WARM = rgba(200, 120, 80)
COOL = rgba(80, 140, 220)
items: list[Input] = []
for mode, x in [(BlendMode.NORMAL, -6.0), (BlendMode.MULTIPLY, -2.0), (BlendMode.SCREEN, 2.0), (BlendMode.ADD, 6.0)]:
    items.append(label(f"BlendMode.{mode.name}", x, 2.1))
    items.append(Rectangle(width=2.4, height=2.4, fillColor=WARM, strokeColor=TRANSPARENT).position(x - 0.6, 0.2))
    items.append(Rectangle(width=2.4, height=2.4, fillColor=COOL, strokeColor=TRANSPARENT).position(x + 0.6, 0.2).blendMode(mode))
close(section(
    "1/12 · Blend modes  —  input.blendMode(BlendMode.MULTIPLY)",
    "how an input's pixels mix with whatever is behind it: multiply darkens the overlap, screen lightens it, add clips to white",
    *items,
))

# ── 2. Chroma key ────────────────────────────────────────────────────────────
greenScreen = np.zeros((240, 320, 3), dtype=np.uint8)
greenScreen[:] = (0, 255, 0)                                     # BGR green
cv2.circle(greenScreen, (160, 120), 70, (40, 140, 255), -1)      # orange subject
greenPng = tempfile.NamedTemporaryFile(suffix=".png", delete=False).name
cv2.imwrite(greenPng, greenScreen)

backdrop = Rectangle(width=9.5, height=3.4, fillColor=rgba(40, 40, 90), strokeColor=TRANSPARENT).position(0, 0.2)
raw = Image(greenPng, width=3.8, height=2.85).position(-2.4, 0.2)
keyed = Image(greenPng, width=3.8, height=2.85).position(2.4, 0.2)
keyed.apply(chromaKey(color=GREEN, tolerance=0.3, softness=0.15), duration=FADE + HOLD + FADE)
close(section(
    "2/12 · Chroma key  —  .apply(chromaKey(GREEN))",
    "green pixels become transparent: the raw footage (left) keeps its green screen, the keyed copy (right) shows the backdrop through it",
    backdrop, raw, keyed, label("raw", -2.4, -1.9), label("chromaKey(GREEN)", 2.4, -1.9),
))

# ── 3. Glow ──────────────────────────────────────────────────────────────────
plain = Circle(radius=1.0, fillColor=rgba(255, 190, 60), strokeColor=TRANSPARENT).position(-2.4, 0.2)
glowing = Circle(radius=1.0, fillColor=rgba(255, 190, 60), strokeColor=TRANSPARENT).position(2.4, 0.2)
glowing.apply(glow(radius=9, intensity=1.2), duration=FADE + HOLD + FADE)
close(section(
    "3/12 · Glow  —  .apply(glow(radius=9))",
    "a blurred copy is additively composited back onto the sharp original — a soft halo, best on bright shapes over dark",
    plain, glowing, label("plain", -2.4, -1.5), label("glow()", 2.4, -1.5),
))

# ── 4. Transitions ───────────────────────────────────────────────────────────
# Incoming card sits *behind* the outgoing one (lower zIndex) until the
# transition starts, so nothing flashes early.
cfOut = Rectangle(width=4.0, height=2.6, fillColor=RED_A, strokeColor=TRANSPARENT, cornerRadius=10).position(-3.0, 0.1).zIndex(2)
cfIn = Rectangle(width=4.0, height=2.6, fillColor=BLUE_C, strokeColor=TRANSPARENT, cornerRadius=10).position(-3.0, 0.1).zIndex(1)
pushOut = Rectangle(width=4.0, height=2.6, fillColor=GREEN_A, strokeColor=TRANSPARENT, cornerRadius=10).position(3.0, 0.1).zIndex(2)
pushIn = Rectangle(width=4.0, height=2.6, fillColor=rgba(240, 170, 60), strokeColor=TRANSPARENT, cornerRadius=10).position(3.0, 0.1).zIndex(1)
crossfade(cfOut, cfIn, start=0.8, duration=0.8)
push(pushOut, pushIn, direction=Direction.LEFT, distance=4.2, start=0.8, duration=0.8)
close(section(
    "4/12 · Transitions  —  crossfade(a, b) · push(a, b, direction=Direction.LEFT)",
    "plain functions that animate TWO inputs at once: the left pair dissolves, the right pair pushes the old card off-frame",
    cfOut, cfIn, pushOut, pushIn, label("crossfade", -3.0, -1.8), label("push", 3.0, -1.8),
), hold=2.0)

# ── 5. Track mattes ──────────────────────────────────────────────────────────
RAINBOW = LinearGradient(
    rgba(255, 60, 60), rgba(255, 200, 40), rgba(60, 220, 120),
    rgba(60, 160, 255), rgba(200, 80, 255),
)
with Context.noRegister():
    letters = Text("MATTE", fontSize=1.6, fillColor=WHITE).inputs
word = CompoundPolygon(*letters).position(0, 0.1)  # matte source — never drawn itself
content = Rectangle(width=8.5, height=2.2, fillColor=RAINBOW, strokeColor=TRANSPARENT).position(0, 0.1).matte(word)
close(section(
    "5/12 · Track mattes  —  content.matte(word)",
    "the rainbow rectangle is drawn only where the word has pixels — the word itself is never rendered, it's pure stencil",
    content,
))

# ── 6. LUT color grade ───────────────────────────────────────────────────────
GRAD = LinearGradient(rgba(255, 40, 40), rgba(255, 210, 40), rgba(60, 230, 120), rgba(60, 150, 255))
ref = Rectangle(width=8, height=1.2, fillColor=GRAD, strokeColor=TRANSPARENT).position(0, 1.1)
graded = Rectangle(width=8, height=1.2, fillColor=GRAD, strokeColor=TRANSPARENT).position(0, -0.7)
graded.apply(lut("assets/luts/warm.cube"), duration=FADE + HOLD + FADE)
close(section(
    '6/12 · LUT color grade  —  .apply(lut("warm.cube"))',
    "a standard Adobe/DaVinci .cube color-lookup file grades the bottom bar warmer — same file format colorists exchange",
    ref, graded, label("no grade", 0, 1.95), label("warm.cube", 0, 0.15),
))

# ── 7. Adjustment layers ─────────────────────────────────────────────────────
c1 = Circle(radius=0.85, fillColor=rgba(240, 50, 50), strokeColor=TRANSPARENT).position(-3, 0.1).zIndex(1)
c2 = Square(side=1.6, fillColor=rgba(50, 120, 255), strokeColor=TRANSPARENT).position(0, 0.1).zIndex(1)
AdjustmentLayer().zIndex(5).apply(grayscale(), duration=FADE + HOLD + FADE)
c3 = Square(side=1.6, fillColor=rgba(255, 170, 40), strokeColor=TRANSPARENT).position(3, 0.1).zIndex(10)
close(section(
    "7/12 · Adjustment layers  —  AdjustmentLayer().zIndex(5).apply(grayscale())",
    "an invisible full-frame layer whose effects grade the flattened composite of everything BELOW its zIndex — the z=10 square escapes it",
    c1, c2, c3, label("z=1 (graded)", -3, -1.3), label("z=1 (graded)", 0, -1.3), label("z=10 (above layer)", 3, -1.3),
))

# ── 8. Video time remapping ──────────────────────────────────────────────────
S = Context.waitOffset            # this section's global start frame
N = int((FADE + 1.8 + FADE) * FRAMERATE)


def drawCounter(img: np.ndarray, i: int) -> None:
    text = str(i)
    (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 2.6, 6)
    cv2.putText(img, text, ((img.shape[1] - tw) // 2, (img.shape[0] + th) // 2),
                cv2.FONT_HERSHEY_SIMPLEX, 2.6, (255, 255, 255), 6)


counterClip = clip(S, N, 480, 120, drawCounter)
rows: list[Input] = []
for name, ramps, y in [
    ("1×", [], 1.5),
    ("freeze", [(S + 30, S + N, 0.0)], 0.1),
    ("reverse", [(S + 30, S + N, -1.0)], -1.3),
]:
    rows.append(Video(counterClip, speedRamps=ramps, width=4.8, height=1.2).position(0.8, y))
    rows.append(label(name, -3.2, y))
close(section(
    "8/12 · Video time remapping  —  Video(speedRamps=[(start, end, rate)])",
    "one clip with a burned-in frame counter, three playbacks: normal · frozen after 1s (rate 0) · reversed after 1s (rate -1)",
    *rows,
), hold=1.8)

# ── 9. Alpha + GIF export ────────────────────────────────────────────────────
checker: list[Input] = []
for row in range(3):
    for col in range(7):
        shade = WHITE | 0.25 if (row + col) % 2 == 0 else WHITE | 0.08
        checker.append(Rectangle(width=0.9, height=0.9, fillColor=shade, strokeColor=TRANSPARENT)
                       .position(-2.7 + col * 0.9, 1.1 - row * 0.9))
glass = Circle(radius=1.5, fillColor=rgba(80, 160, 255) | 0.55, strokeColor=TRANSPARENT).position(0, 0.2)
close(section(
    "9/12 · Alpha + GIF export  —  --generate out.mov / out.webm / out.gif",
    "the output extension picks the codec: .mov (ProRes 4444) and .webm (VP9) keep real per-pixel alpha, .gif gets a palette pass",
    *checker, glass,
))

# ── 10. Motion tracking ──────────────────────────────────────────────────────
S = Context.waitOffset
N = int((FADE + 1.8 + FADE) * FRAMERATE)
SQ, X0, Y0 = 26, 30, 118


def drawSquare(img: np.ndarray, i: int) -> None:
    x, y = X0 + i * 3, Y0 - i * 1
    cv2.rectangle(img, (x, y), (x + SQ, y + SQ), (255, 255, 255), -1)


squareClip = clip(S, N, 320, 180, drawSquare)
video = Video(squareClip, width=7.2, height=4.05).position(0, -0.1)
path = video.track(X0 + SQ / 2, Y0 + SQ / 2, startFrame=S, endFrame=S + N)
ring = Circle(radius=0.32, fillColor=TRANSPARENT, strokeColor=rgba(255, 60, 60), strokeWidth=0.06)
ring.attachTo(path)
close(section(
    "10/12 · Motion tracking  —  ring.attachTo(video.track(x, y))",
    "real OpenCV optical flow follows the white square through the clip; the red ring is a separate Input pinned to the tracked point",
    video, ring,
), hold=1.8)

# ── 11. Beat-sync ────────────────────────────────────────────────────────────
S = Context.waitOffset
RATE, CLICK = 22050, int(0.03 * 22050)
samples = [0.0] * int(3.0 * RATE)
for beatTime in (0.5, 1.0, 1.5, 2.0, 2.5):
    at = int(beatTime * RATE)
    for i in range(CLICK):
        samples[at + i] = random.uniform(-1.0, 1.0) * (1.0 - i / CLICK)
clickWav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
with wave.open(clickWav, "wb") as wv:
    wv.setnchannels(1)
    wv.setsampwidth(2)
    wv.setframerate(RATE)
    wv.writeframes(struct.pack(f"<{len(samples)}h", *(int(s * 32767) for s in samples)))

sound = Sound(clickWav, start=S * SINGLE_FRAME)   # audio aligned to this section in the export
logo = Circle(radius=0.9, fillColor=rgba(255, 150, 40), strokeColor=TRANSPARENT).position(0, 0.1)
for beat in sound.beats():
    logo.apply(pulse(scale=1.35, start=beat, duration=0.3))
close(section(
    "11/12 · Beat-sync  —  for beat in sound.beats(): logo.apply(pulse(start=beat))",
    "spectral-flux onset detection finds every click in a real audio file; the circle pulses exactly on each detected beat",
    logo,
), hold=0.4)

# ── 12. Auto-captions ────────────────────────────────────────────────────────
S = Context.waitOffset
speech = Sound("test/test_speech.wav", start=S * SINGLE_FRAME)
srtPath = speech.transcribe(model="tiny", language="en")
subs = Subtitles(srtPath, fontSize=0.5)  # times its own cues — not part of the section group
close(section(
    "12/12 · Auto-captions  —  Subtitles(sound.transcribe())",
    "faster-whisper transcribes real recorded speech into a standard .srt at build time; the existing Subtitles input renders the cues",
), hold=2.6)
