#!/usr/bin/env python3


from videocode.VideoCode import *
from videocode.template.chess.chessboard import *

# TODO: chess template
# c = ChessBoard()
# c.play(1)

# TODO: group
# g = (
#     group(
#         square(),
#         circle(),
#     )
#     .position(*CENTER)
#     .moveTo(x=0.7 * SW)
#     .flush()
#     .apply(grayscale())
#     .moveTo(x=0.5 * SW)
#     .flush()
# )

# TODO: image test
# i = image("wb.png").position(*CENTER).scale(2)
# i.moveTo(0.7 * SW)

# TODO: circle test
r1 = rectangle(width=100).position(x=0.5 * SW, y=200).align(y=0, x=0)
r2 = rectangle(width=100, color=RED).position(x=0.5 * SW, y=200).align(y=0.5, x=0.5).apply(grayscale(), start=SF * 2, duration=SF * 10)
g = group(r1, r2)

for i in range(13):
    # r.width += 20
    r1.rotate(90 / 12 * i)
    r2.rotate(90 / 12 * i)

    r1.flush()
    r2.flush()
