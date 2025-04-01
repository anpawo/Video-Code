from videocode.VideoCode import *

x = 700
y = 50

group(
    square(filled=True, cornerRadius=30, thickness=20).setPosition(x, y + 200),
    circle(filled=True, color=RED).setPosition(x, y + 500),
    rectangle(cornerRadius=0, thickness=8, color=GREEN).setPosition(x + 400, y + 350),
).apply(
    moveTo(
        0.5,
        0.5,
    ),
).add().apply(
    moveTo(
        0.5,
        0.1,
    ),
).add()
