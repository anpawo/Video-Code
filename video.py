#!/usr/bin/env python3


from videocode.VideoCode import *
from videocode.template.chess.chessboard import *

a = image("hehe.jpg").apply(blur(1)).apply(scale(3)).setPosition((203*3/2), (360*3/2)).add()
i = image("hehe.jpg").apply(blur(10)).apply(scale(3)).setPosition(*MIDDLE).add()
b = image("hehe.jpg").apply(blur(1000)).apply(scale(3)).setPosition(1600 , (360*3/2)).add()
