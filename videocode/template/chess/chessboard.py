#!/usr/bin/env python3


import re

from videocode.Constant import MIDDLE, SH, SW
from videocode.input.media.WebImage import webImage
from videocode.transformation.size.Scale import scale


type Color = bool
type Piece = int


KING = 0
QUEEN = 1
ROOK = 2
BISHOP = 3
KNIGHT = 4
PAWN = 5
BOARD = 6

BLACK = False
WHITE = True

BOARD_URL = "https://assets-themes.chess.com/image/9rdwe/200.png"

FILE = {
    "a": 0,
    "b": 1,
    "c": 2,
    "d": 3,
    "e": 4,
    "f": 5,
    "g": 6,
    "h": 7,
}


RANK = {
    "1": 0,
    "2": 1,
    "3": 2,
    "4": 3,
    "5": 4,
    "6": 5,
    "7": 6,
    "8": 7,
}


PIECE = {
    KING: "K",
    QUEEN: "Q",
    ROOK: "R",
    BISHOP: "B",
    KNIGHT: "N",
    PAWN: "",
}

URL = {
    KING: "k",
    QUEEN: "q",
    ROOK: "r",
    BISHOP: "b",
    KNIGHT: "n",
    PAWN: "p",
}


class ChessBoard:
    def __init__(self, pgn: str | None = None, *, whitePlays=True, board: str | None = None) -> None:
        """
        Portable Game Notation

        1 2
        0 1

        """
        self.pgn = self.splitPGN(pgn) if pgn else []
        self.default: list[list[tuple[Color, Piece] | None]] = [
            [(BLACK, ROOK), (BLACK, KNIGHT), (BLACK, BISHOP), (BLACK, QUEEN), (BLACK, KING), (BLACK, BISHOP), (BLACK, KNIGHT), (BLACK, ROOK)],
            [(BLACK, PAWN) for _ in range(8)],
            [None for _ in range(8)],
            [None for _ in range(8)],
            [None for _ in range(8)],
            [None for _ in range(8)],
            [(WHITE, PAWN) for _ in range(8)],
            [(WHITE, ROOK), (WHITE, KNIGHT), (WHITE, BISHOP), (WHITE, QUEEN), (WHITE, KING), (WHITE, BISHOP), (WHITE, KNIGHT), (WHITE, ROOK)],
        ]
        self.board = self.default  # or starting position
        self.inputs = {}

        self.addInputs()

    def addInputs(self):
        self.inputs[BOARD] = webImage(BOARD_URL).setPosition(*MIDDLE).apply(scale(0.5)).add()

        defaultScaling = 0.7
        ox = 0.3175 * SW
        oy = 0.175 * SH
        tileSize = 100.2

        for y, row in enumerate(self.board):
            for x, col in enumerate(row):
                # Empty
                if col is None:
                    continue

                self.inputs[col] = webImage(self.getUrl(*col)).setPosition(ox + x * tileSize, oy + y * tileSize).apply(scale(0.7)).add()

    def splitPGN(self, pgn: str):
        return [i.split() for i in re.split(r"\d+\.\s", pgn.split("\n\n1.")[1])]

    def getUrl(self, color: Color, piece: Piece):
        return f"https://assets-themes.chess.com/image/ejgfv/150/{'w' if color else 'b'}{URL[piece]}.png"


if __name__ == "__main__":
    c = ChessBoard(
        """[Event "Live Chess"]
[Site "Chess.com"]
[Date "2025.11.24"]
[Round "?"]
[White "DrBen1834"]
[Black "MROUSSET"]
[Result "0-1"]
[TimeControl "180+2"]
[WhiteElo "569"]
[BlackElo "591"]
[Termination "MROUSSET a gagné par échec et mat"]
[ECO "C00"]
[EndTime "11:22:33 GMT+0000"]
[Link "https://www.chess.com/game/live/145896894352?move=0"]

1. e4 e6 2. Nf3 d5 3. exd5 exd5 4. Bd3 Nf6 5. O-O Nc6 6. Re1+ Be7 7. b3 O-O 8.
Ng5 h6 9. Nf3 Nb4 10. Qe2 Re8 11. Bb5 c6 12. Bxc6 bxc6 13. Nd4 Bg4 14. f3 Bh5
15. c3 Qb6 16. cxb4 Qxd4+ 17. Kh1 Qxa1 18. Nc3 d4 19. Bb2 Qxb2 20. Rb1 Qa3 21.
Na4 Bxb4 22. Qc4 Bxd2 23. Qxd4 Qxa2 24. Rd1 Ba5 25. Nc5 Qxb3 26. Nxb3 Bb6 27.
Qd6 Rad8 28. Qxd8 Rxd8 29. Rxd8+ Bxd8 30. Nc5 a5 31. Kg1 Bb6 32. Kf1 Bxc5 33.
Ke1 Nd5 34. Kd2 a4 35. Kc2 a3 36. Kb3 Ne3 37. g4 Bg6 38. h4 h5 39. g5 f6 40.
gxf6 gxf6 41. Ka2 Bf7+ 42. Ka1 Bd4+ 43. Kb1 a2+ 44. Kc1 a1=Q+ 45. Kd2 Qc3+ 46.
Ke2 Bc4+ 47. Kf2 Ng4+ 48. Kg3 f5 49. Kf4 Qe3+ 50. Kxf5 Qe5+ 51. Kg6 Bf7# 0-1"""
    )

    print(c.pgn)
    print(c.default)
