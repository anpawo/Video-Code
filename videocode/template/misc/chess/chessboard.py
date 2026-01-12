#!/usr/bin/env python3


import math
import chess.pgn


from videocode.input.media.WebImage import webImage
from videocode.input.input import Input
from videocode.effect.effect.Scale import scale
from videocode.utils.easings import Easing
from videocode.globals import wait


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

BOARD_URL = "https://assets-themes.chess.com/image/9rdwe/200.png"


class ChessBoard:
    def __init__(self, pgn="pgn") -> None:
        # GameState
        with open(pgn) as f:
            game = chess.pgn.read_game(f)
        if game is None:
            raise ValueError("Invalid Portable Game Notation (pgn).")
        self.game = game
        self.board = self.game.board()

        # Pieces Video Position
        self.defaultScaling = 0.7
        self.ox = 0.3175 * SW
        self.oy = 0.175 * SH
        self.tileSize = 100.2

        # Inputs
        self.boardInput = webImage(BOARD_URL).position(*CENTER).apply(scale(0.5)).flush()
        self.pieces: dict[Position, tuple[webImage, tuple[Color, Piece]]] = {}
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
                webImage(self.getUrl(color, piece)).position(self.ox + x * self.tileSize, self.oy + y * self.tileSize).apply(scale(self.defaultScaling)).flush(),
                (color, piece),
            )
            x += 1

    def getUrl(self, color: Color, piece: Piece):
        """
        https://assets-themes.chess.com/image/ejgfv/150/wb.png
        """
        return f"https://assets-themes.chess.com/image/ejgfv/150/{'w' if color == WHITE else 'b'}{piece}.png"

    def play(self, nMove: int):
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
            self.pieces[(sx, sy)][0].moveTo(self.ox + dx * self.tileSize, self.oy + dy * self.tileSize, easing=Easing.Linear, duration=duration).flush()
            wait(duration - SF)
            # TODO: bring back hide
            # if (dx, dy) in self.pieces:
            #     self.pieces[(dx, dy)][0].hide()
            self.pieces[(dx, dy)] = self.pieces[(sx, sy)]
            del self.pieces[(sx, sy)]
            if move.promotion:
                self.pieces[(dx, dy)] = self.pieces[(dx, dy)][0], (self.pieces[(dx, dy)][1][0], chess.PIECE_SYMBOLS[move.promotion])
                self.pieces[(dx, dy)][0].url = self.getUrl(*self.pieces[(dx, dy)][1])

            wait(0.1)
            nMove -= 1
            if nMove == 0:
                return


if __name__ == "__main__":
    r = ChessBoard()
