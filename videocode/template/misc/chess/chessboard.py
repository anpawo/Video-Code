#!/usr/bin/env python3

from __future__ import annotations

import math


import os

from videocode.constants import SF
from videocode.input.media.Image import Image
from videocode.utils.bezier import Easing
from videocode.context import wait


type Color = bool
type Piece = str
type Position = tuple[int, int]


KING = 0
QUEEN = 1
ROOK = 2
BISHOP = 3
KNIGHT = 4
PAWN = 5

BLACK = False
WHITE = True

# The board and the twelve pieces live in the repository, not on chess.com.
# They used to be fetched by `WebImage` AT BAKE TIME, which meant this scene
# could not be built offline, its goldens depended on a third party's server,
# and it was the one thing keeping the corpus from running anywhere but the
# author's machine. Provenance of the files, so they can be refreshed:
#   board  https://assets-themes.chess.com/image/9rdwe/200.png
#   pieces https://assets-themes.chess.com/image/ejgfv/150/{w|b}{k,q,r,b,n,p}.png
# Relative, like `Image("wb.png")` and `ChessBoard("pgn")` beside it: a scene
# is executed from the project root. An absolute path would also work for
# opening the file and would still be wrong — it travels into Context.stack, so
# the same scene would hash differently on two machines. The bake digest caught
# exactly that, from a second checkout of this repository.
ASSET_DIR = os.path.join("assets", "chess")


class ChessBoard:
    def __init__(self, pgn="pgn") -> None:
        # Imported lazily: python-chess computes its attack tables at import
        # (~100ms) — scenes that don't build a ChessBoard shouldn't pay for it.
        import chess.pgn

        # GameState
        with open(pgn) as f:
            game = chess.pgn.read_game(f)
        if game is None:
            raise ValueError("Invalid Portable Game Notation (pgn).")
        self.game = game
        self.board = self.game.board()

        # Pieces Video Position
        self.defaultScaling = 0.7
        self.ox = -2.92
        self.oy = -2.92
        self.tileSize = 0.835

        # Inputs
        self.boardInput = Image(os.path.join(ASSET_DIR, "board.png")).scale(0.5).flush()
        self.pieces: dict[Position, tuple[Image, tuple[Color, Piece]]] = {}
        self.addInputs()

    def addInputs(self):
        # Current Position
        fen = self.board.fen().split()[0]
        x = 0
        y = 0

        for c in fen:
            # Next Line
            if c == "/":
                x = 0
                y += 1
                continue

            # Empty Squares
            elif c in "123456789":
                x += int(c)
                continue

            # Piece
            color = WHITE if c.isupper() else BLACK
            piece = c.lower()
            self.pieces[(x, y)] = (
                Image(self._pieceFile(color, piece))
                .position(
                    self.ox + x * self.tileSize,
                    self.oy + y * self.tileSize,
                )
                .scale(self.defaultScaling)
                .flush(),
                (color, piece),
            )
            x += 1

    def _pieceFile(self, color: Color, piece: Piece) -> str:
        """assets/chess/wb.png — white bishop, black king is `bk.png`."""
        return os.path.join(ASSET_DIR, f"{'w' if color == WHITE else 'b'}{piece}.png")

    def play(self, nMove: int | None = None):
        import chess  # already loaded by __init__; this is just a name lookup

        for move in self.game.mainline_moves():
            sx, sy = move.from_square % 8, 7 - move.from_square // 8
            dx, dy = move.to_square % 8, 7 - move.to_square // 8
            distance = math.sqrt((sx - dx) ** 2 + (sy - dy) ** 2)
            duration = min(distance * 0.2, 0.5)

            # Castle
            if (uci := move.uci()) in ["e1g1", "e1c1", "e8g8", "e8c8"]:
                color = self.pieces[(sx, sy)][1][0]
                queenside = "c" in uci

                sxr = 0 if queenside else 7
                syr = 7 if color == WHITE else 0
                dxr = 3 if queenside else 5
                dyr = 7 if color == WHITE else 0

                # Move Rook
                self.pieces[(sxr, syr)][0].moveTo(self.ox + dxr * self.tileSize, self.oy + dyr * self.tileSize, easing=Easing.Linear, duration=duration).flush()
                self.pieces[(dxr, dyr)] = self.pieces[(sxr, syr)]
                del self.pieces[(sxr, syr)]

            # En Passant
            elif 0:
                raise ValueError("En Passant not yet implemented")

            # Normal Move
            mover = self.pieces[(sx, sy)][0]
            mover.moveTo(self.ox + dx * self.tileSize, self.oy + dy * self.tileSize, easing=Easing.Linear, duration=duration).flush()
            if (dx, dy) in self.pieces:
                self.pieces[(dx, dy)][0].waitTo(mover.meta.transformationOffset).hide().flush()
            wait(duration - SF)
            self.pieces[(dx, dy)] = self.pieces[(sx, sy)]
            del self.pieces[(sx, sy)]
            if move.promotion:
                # Image textures are fixed at creation — swap the pawn for a
                # freshly-created piece image rather than mutating its filepath.
                color = self.pieces[(dx, dy)][1][0]
                piece = chess.PIECE_SYMBOLS[move.promotion]
                target = mover.meta.transformationOffset
                promoted = (
                    Image(self._pieceFile(color, piece))
                    .position(self.ox + dx * self.tileSize, self.oy + dy * self.tileSize)
                    .scale(self.defaultScaling)
                )
                if target > promoted.meta.transformationOffset:
                    promoted.hide()
                    promoted.waitTo(target)
                    promoted.show().flush()
                mover.hide().flush()
                self.pieces[(dx, dy)] = (promoted, (color, piece))

            wait(0.1)
            if nMove is not None:
                nMove -= 1
                if nMove == 0:
                    return


if __name__ == "__main__":
    r = ChessBoard()
