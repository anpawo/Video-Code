#!/usr/bin/env python3

import chess.pgn

from io import StringIO

pgn = """[Event "Live Chess"]
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

game = chess.pgn.read_game(StringIO(pgn))
board = game.board()

for move in game.mainline_moves():
    print(move)
    break
    board.push(move)
    # print(board)  # ASCII board
    # print(board.fen())  # FEN of this position
