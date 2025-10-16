
```py
from videocode.VideoCode import *

x = 700
y = 50

# Set the automatic adder on because we only do one action at a time.
automaticAdderOn()

### ===> Creating shapes and setting their positions
g = (
    group(
        # image("assets/icon.png").setPosition(0.5, 0.5),
        # video("assets/v.mp4").setPosition(0.5, 0.5),
        c := circle(filled=True, color=RED).setPosition(x, y + 500),
        s := square(filled=True, cornerRadius=30, thickness=20).setPosition(x, y + 200),
        r := rectangle(cornerRadius=0, thickness=8, color=GREEN).setPosition(x + 400, y + 350),
    )
    # .apply(fadeIn())
    .apply(moveTo(0.5, 0.5))
)

# Set the automatic adder off because we do more than one action; we change the position and then augment the radius' size.
# We could join them both into one apply and keep the automatic adder.
automaticAdderOff()

### ===> Changing the circle and the rectangle
for i in range(0, 40):
    c.radius += 1
    r.width += 10
    r.height -= 2
    g.add()

# Separate
wait(0)

### ===> Changing the square
for i in range(0, 30):
    s.cornerRadius += 2
    s.add()
```
