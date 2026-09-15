#!/usr/bin/env python3

"""
Assertion-based tests for the montage effects pack:
- camera moves (punchIn / zoomTo / snapZoom / travelling) and their framing maths
- impact — punch + damped rumble that lands exactly where it started
- whipPan — position throw with a blur that peaks mid-move
- spotlightOn / zoneFocus — the frame-UV spotlight shader binding
- desaturate / glitchBurst / vignetteBeat / scope
- retime — the speedRamp builders that are NOT effects
Run directly: `python3 test/montage_effects_test.py`
"""

import sys

sys.path.insert(0, ".")
sys.path.insert(0, "test")
from helpers import check, section, summary

from videocode import *
from videocode.template.effect.framing import framePosition, mediaBox
from videocode.template.effect.other.camera import punchIn, snapZoom, travelling, zoomTo
from videocode.template.effect.other.desaturate import desaturate
from videocode.template.effect.other.glitchBurst import glitchBurst
from videocode.template.effect.other.impact import impact
from videocode.template.effect.other.retime import accelere, freezeFrame, ralenti, rewind
from videocode.template.effect.other.scope import scope, unscope
from videocode.template.effect.other.spotlightOn import spotlightOn, zoneFocus
from videocode.template.effect.other.vignetteIn import vignetteBeat, vignetteIn
from videocode.template.effect.other.whipPan import whipPan


def framesWith(index: int, key: str) -> dict[int, dict]:
    return {f: entry[key] for f, entry in Context.stack[index].items() if f != -1 and key in entry}


def last(frames: dict[int, dict]) -> dict:
    return frames[max(frames)]["args"]


# ---------------------------------------------------------------------------
section("framing — fractions of the media's own box")

box = Rectangle(width=4, height=2).position(0.0, 0.0)
mb = mediaBox(box)
check("mediaBox reads the vertices", (mb.x, mb.y) == (4.0, 2.0))
centre = framePosition(box, 0.5, 0.5, 1.0)
check("centre maps to the frame centre", abs(centre.x) < 1e-9 and abs(centre.y) < 1e-9)
# Top-left of the media has to travel DOWN-RIGHT to reach the centre of the
# frame: +x, -y. Getting that sign wrong is the classic framing bug.
tl = framePosition(box, 0.0, 0.0, 1.0)
check("top-left frames to (+2, -1)", abs(tl.x - 2.0) < 1e-9 and abs(tl.y + 1.0) < 1e-9)
tl2 = framePosition(box, 0.0, 0.0, 2.0)
check("zoom scales the offset", abs(tl2.x - 4.0) < 1e-9 and abs(tl2.y + 2.0) < 1e-9)

# ---------------------------------------------------------------------------
section("punchIn — scale only, position untouched")

p = Rectangle(width=2, height=1).position(1.0, 1.0)
before = set(framesWith(p.meta.index, "Position"))
p.apply(punchIn(zoom=1.5, duration=1.0))
scales = framesWith(p.meta.index, "Scale")
check("punchIn reaches 1.5x", abs(last(scales)["x"] - 1.5) < 1e-6)
# The `.position(1, 1)` above already wrote frame 0; what matters is that the
# effect adds nothing of its own, so a concurrent move survives it.
check("punchIn claims no position of its own", set(framesWith(p.meta.index, "Position")) == before)

# ---------------------------------------------------------------------------
section("zoomTo — the target point lands at the frame centre")

z = Rectangle(width=4, height=2).position(0.0, 0.0)
z.apply(zoomTo(x=0.25, y=0.75, zoom=2.0, duration=1.0))
scales, pos = framesWith(z.meta.index, "Scale"), framesWith(z.meta.index, "Position")
check("zoomTo reaches 2x", abs(last(scales)["x"] - 2.0) < 1e-6)
# (0.25, 0.75) is one quarter left and one quarter down: at 2x that is
# (+2, +1) of correction.
check("zoomTo frames the point", abs(last(pos)["x"] - 2.0) < 1e-6 and abs(last(pos)["y"] - 1.0) < 1e-6)
check("zoom and pan share frames", set(scales) == set(pos))

# ---------------------------------------------------------------------------
section("snapZoom — returns exactly to the original framing")

s = Rectangle(width=4, height=2).position(0.0, 0.0)
s.apply(snapZoom(x=0.2, y=0.2, zoom=3.0, hold=0.5, attack=0.1, release=0.3))
scales, pos = framesWith(s.meta.index, "Scale"), framesWith(s.meta.index, "Position")
check("snapZoom peaks at 3x", abs(max(e["args"]["x"] for e in scales.values()) - 3.0) < 1e-6)
check("snapZoom ends back at 1x", abs(last(scales)["x"] - 1.0) < 1e-6)
check("snapZoom ends back at origin", abs(last(pos)["x"]) < 1e-6 and abs(last(pos)["y"]) < 1e-6)

# ---------------------------------------------------------------------------
section("travelling — fixed zoom, moving frame")

t = Rectangle(width=4, height=2).position(0.0, 0.0)
t.apply(travelling(fromX=0.0, fromY=0.5, toX=1.0, toY=0.5, zoom=2.0, duration=1.0))
scales, pos = framesWith(t.meta.index, "Scale"), framesWith(t.meta.index, "Position")
check("travelling sets the zoom once", len(scales) == 1 and abs(last(scales)["x"] - 2.0) < 1e-6)
xs = [e["args"]["x"] for _, e in sorted(pos.items())]
check("travelling pans left edge -> right edge", abs(xs[0] - 4.0) < 1e-6 and abs(xs[-1] + 4.0) < 1e-6)
check("travelling holds y", all(abs(e["args"]["y"]) < 1e-9 for e in pos.values()))

# ---------------------------------------------------------------------------
section("impact — punch + rumble, back to zero")

i = Rectangle(width=2, height=1).position(0.5, -0.5)
i.apply(impact(zoom=1.4, amplitude=0.2, duration=0.8))
scales, pos = framesWith(i.meta.index, "Scale"), framesWith(i.meta.index, "Position")
check("impact peaks above 1.4x", max(e["args"]["x"] for e in scales.values()) >= 1.4 - 1e-6)
check("impact ends at 1x", abs(last(scales)["x"] - 1.0) < 1e-6)
check("impact ends at its origin", abs(last(pos)["x"] - 0.5) < 1e-6 and abs(last(pos)["y"] + 0.5) < 1e-6)
check("impact actually rumbles", max(abs(e["args"]["x"] - 0.5) for e in pos.values()) > 0.05)

# ---------------------------------------------------------------------------
section("whipPan — blur peaks mid-throw, gone at the ends")

w = Rectangle(width=4, height=2).position(0.0, 0.0)
w.apply(whipPan(toX=1.0, toY=0.5, blur=12, duration=0.6))
blurs = framesWith(w.meta.index, "Blur")
amounts = [e["args"]["strength"] for _, e in sorted(blurs.items())]
check("whipPan blurs", len(amounts) > 0)
check("whipPan blur peaks in the middle", amounts[len(amounts) // 2] == max(amounts))
check("whipPan blur peak <= requested", max(amounts) <= 12 + 1e-6)
check("whipPan ends sharp", max(framesWith(w.meta.index, "Position")) > max(blurs))

# ---------------------------------------------------------------------------
section("spotlight — frame-UV pool of light")

sp = spotlight(x=0.25, y=0.75, width=0.4, height=0.2, corner=0.5, softness=0.02, darkness=0.9)
check("spotlight centre", sp.centerX == 0.25 and sp.centerY == 0.75)
check("spotlight stores half extents", sp.halfWidth == 0.2 and sp.halfHeight == 0.1)
check("spotlight corner/softness/darkness", sp.corner == 0.5 and sp.softness == 0.02 and sp.darkness == 0.9)
# The GLSL reads p[] alphabetically by attribute name. Pin that order here:
# renaming an attribute silently reshuffles the push constants.
check(
    "spotlight attribute order is the documented one",
    sorted(vars(sp)) == ["centerX", "centerY", "corner", "darkness", "halfHeight", "halfWidth", "softness"],
)

sl = Rectangle(width=2, height=1)
sl.apply(spotlightOn(x=0.4, y=0.6, radius=0.2, duration=1.0, fade=0.3))
spots = framesWith(sl.meta.index, "Spotlight")
darks = [e["args"]["darkness"] for _, e in sorted(spots.items())]
check("spotlightOn fades in and back out", darks[0] < darks[len(darks) // 2] and darks[-1] < darks[len(darks) // 2])
check("spotlightOn keeps the pool round", abs(spots[max(spots)]["args"]["halfWidth"] * SCREEN_WIDTH
                                              - spots[max(spots)]["args"]["halfHeight"] * SCREEN_HEIGHT) < 1e-6)

zf = Rectangle(width=2, height=1)
zf.apply(zoneFocus(x=0.5, y=0.5, width=0.6, height=0.4, corner=0.0, duration=1.0))
zones = framesWith(zf.meta.index, "Spotlight")
check("zoneFocus keeps its rectangle", abs(zones[max(zones)]["args"]["halfWidth"] - 0.3) < 1e-6)

# ---------------------------------------------------------------------------
section("desaturate / glitchBurst / vignette / scope")

d = Rectangle(width=1, height=1)
d.apply(desaturate(amount=1.0, duration=1.2, fade=0.3))
grays = [e["args"]["strength"] for _, e in sorted(framesWith(d.meta.index, "Grayscale").items())]
check("desaturate rises then falls", grays[len(grays) // 2] > grays[0] and grays[len(grays) // 2] > grays[-1])

# Le palier, pas seulement les deux rampes. Un shader fragment ne vaut que pour
# la frame ou il est pose : tant que le palier n'etait emis qu'une fois, les
# frames du milieu n'en recevaient aucun et l'effet disparaissait entre son
# entree et sa sortie — visible a l'image, invisible pour les assertions
# ci-dessus, qui ne regardaient que le debut, le milieu et la fin de la LISTE.
dh = Rectangle(width=1, height=1)
dh.apply(desaturate(amount=1.0, duration=1.2, fade=0.3))
held = sorted(framesWith(dh.meta.index, "Grayscale"))
check("desaturate n'a pas de trou", held == list(range(min(held), max(held) + 1)))

sh = Rectangle(width=1, height=1)
sh.apply(spotlightOn(x=0.5, y=0.5, radius=0.2, duration=1.2, fade=0.3))
lit = sorted(framesWith(sh.meta.index, "Spotlight"))
check("spotlightOn n'a pas de trou", lit == list(range(min(lit), max(lit) + 1)))
check("spotlightOn couvre bien sa duree", len(lit) >= round(1.2 * FRAMERATE) - 1)

g = Rectangle(width=1, height=1)
g.apply(glitchBurst(amount=6, slices=16, seed=7, blocks=30, duration=0.6))
glitches = framesWith(g.meta.index, "Glitch")
check("glitchBurst emits ONE glitch window", len({e["args"]["seed"] for e in glitches.values()}) == 1)
check("glitchBurst keeps its seed", glitches[min(glitches)]["args"]["seed"] == 7)
check("glitchBurst blocks up first", len(framesWith(g.meta.index, "Pixelate")) > 0)

v = Rectangle(width=1, height=1)
v.apply(vignetteBeat(intensity=0.8, duration=1.0))
vs = [e["args"]["intensity"] for _, e in sorted(framesWith(v.meta.index, "Vignette").items())]
check("vignetteBeat opens back up", abs(vs[0]) < 1e-6 and abs(vs[-1]) < 1e-6 and max(vs) > 0.7)

vi = Rectangle(width=1, height=1)
vi.apply(vignetteIn(intensity=0.5, duration=1.0))
check("vignetteIn persists at full intensity",
      abs([e["args"]["intensity"] for _, e in sorted(framesWith(vi.meta.index, "Vignette").items())][-1] - 0.5) < 1e-6)

sc = Rectangle(width=1, height=1)
sc.apply(scope(ratio=2.39, duration=0.5))
bars = [e["args"]["top"] for _, e in sorted(framesWith(sc.meta.index, "Crop").items())]
expected = max(0.0, (1.0 - (SCREEN_WIDTH / 2.39) / SCREEN_HEIGHT) / 2) * 100
check("scope closes to the 2.39:1 bar height", abs(bars[-1] - expected) < 1e-6)
check("scope starts from nothing", abs(bars[0]) < 1e-6)

us = Rectangle(width=1, height=1)
us.apply(unscope(ratio=2.39, duration=0.5))
openBars = [e["args"]["top"] for _, e in sorted(framesWith(us.meta.index, "Crop").items())]
check("unscope opens back to zero", abs(openBars[-1]) < 1e-6 and abs(openBars[0] - expected) < 1e-6)

# ---------------------------------------------------------------------------
section("retime — speedRamp builders, in seconds")

check("ralenti slows", ralenti(at=1, duration=2, rate=0.4) == (FRAMERATE, 3 * FRAMERATE, 0.4))
check("accelere speeds up", accelere(at=0, duration=1, rate=4)[2] == 4.0)
check("freezeFrame holds", freezeFrame(at=2, duration=1)[2] == 0.0)
check("rewind goes backwards", rewind(at=2, duration=1)[2] < 0)
check("a zero-length window still spans one frame", ralenti(at=1, duration=0)[1] > ralenti(at=1, duration=0)[0])

# A Video accepts them as-is — that is the whole contract.
ramps = [ralenti(at=0, duration=1), accelere(at=2, duration=1), freezeFrame(at=4, duration=1)]
check("Video accepts the builders' output", all(isinstance(r, tuple) and len(r) == 3 for r in ramps))

# ---------------------------------------------------------------------------
summary()
