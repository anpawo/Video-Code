#!/usr/bin/env python3


from videocode.template.input._inputs import *
from videocode import *

p = Plane()

# Stroke stress test — same characteristics as the big B (RED fill, WHITE
# stroke, strokeWidth=0.2) at a smaller fontSize, with every glyph class
# that historically broke the stroke renderer:
#   - counters/holes: a b d e g o p q  /  Q O 0 8
#   - multiple contours (dots): i j ! ? ; :
#   - tight junctions like B's bowls: B K R X M W &
#   - tight curves and S-bends: S 3 s % @
common = dict(fontSize=1, fillColor=RED, strokeColor=WHITE, strokeWidth=0.05)

Text("abdegopq", **common).position(y=2.7)
Text("ij!?;:", **common).position(y=0.9)
Text("BKRXMW&", **common).position(y=-0.9)
Text("QO08S3s%@", **common).position(y=-2.7)
