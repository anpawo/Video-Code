#!/usr/bin/env python3

# Visual regression scene — ChessBoard template.
# Exercises WebImage (Create + texture), Position/Scale broadcasting, moveTo
# animation, and mid-timeline hide/show (capture disappearance).

from videocode import *
from videocode.template.misc.chess.chessboard import ChessBoard

ChessBoard("pgn").play(nMove=6)
