#!/usr/bin/env python3


from videocode.template.input._inputs import *
from videocode import *
from videocode.utils.bezier import Easing
from videocode.utils.classutils import At

p = Plane()

# Animated radial gradient "wave" (#124 follow-up demo) — a bright ring
# sweeps from each glyph's center out to its edge and repeats. Both "O" and
# "@" have holes, so the wave is invisible while inside the counter and only
# appears once it reaches the visible ring — driven every frame by a
# Bezier-eased range over the gradient's middle stop position.
oText  = Text("O", fontSize=3, fillColor=RadialGradient(BLUE_B, (WHITE, 0), RED)).position(x=-2.5)
atText = Text("@", fontSize=3, fillColor=RadialGradient(GREEN_A, (WHITE, 0), RED)).position(x=2.5)

waveDuration  = 1.5  # seconds for one outward sweep
numWaves      = 4
framesPerWave = int(waveDuration * FRAMERATE)

for wave in range(numWaves):
    for pos, i in Easing.InOut.rangeIdx(0, 100, waveDuration):
        frame = wave * framesPerWave + i
        oText.fillColor  = At(start=frame * SF, duration=SF) | RadialGradient(BLUE_B, (WHITE, pos), RED)
        atText.fillColor = At(start=frame * SF, duration=SF) | RadialGradient(GREEN_A, (WHITE, pos), RED)
