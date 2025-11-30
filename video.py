#!/usr/bin/env python3


from videocode.VideoCode import *
from videocode.template.chess.chessboard import *

# TODO: chess template
# chess = ChessBoard()

# TODO: Camera Transformation
g = (
    group(
        c := circle(),
        square(),
    )
    .setPosition(0, SH * 0.5)
    .add()
)

cam = camera().setPosition(0, 0).moveTo(-0.5 * SW, duration=1).apply(scale(2)).add()

wait()

# c.color = GREEN
# c.add()  # Needs a fix
