from videocode.VideoCode import *

x = 700
y = 50

group(
    square(filled=True, cornerRadius=30, thickness=20, duration=2).setPosition(x, y + 175),
    circle(filled=True, color=RED, duration=2).setPosition(x, y + 500),
    rectangle(cornerRadius=0, thickness=8, color=GREEN, duration=2).setPosition(x + 300, y + 300),
).apply(
    fadeIn()
).apply(move(250, 250), startTime=1).add()
