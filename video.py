#!/usr/bin/env python3


from videocode.VideoCode import *
from videocode.template.chess.chessboard import *

# TODO: chess template
# chess = ChessBoard()

# TODO: Camera shaders
g = (
    group(
        circle(),
        square(),
    )
    .setPosition(0, SH * 0.5)
    .add()
)

c = camera().setPosition(0, 0).moveTo(-0.5 * SW).add()
