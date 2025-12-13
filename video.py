#!/usr/bin/env python3


from videocode.VideoCode import *
from videocode.template.chess.chessboard import *

# TODO: chess template
c = ChessBoard()
c.play(1)

# g = (
#     group(
#         square(),
#         circle(),
#     )
#     .setPosition(*MIDDLE)
#     .moveTo(x=0.7 * SW)
#     .add()
#     .apply(grayscale())
#     .moveTo(x=0.5 * SW)
#     .add()
# )
