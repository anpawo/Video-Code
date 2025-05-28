
```py
from videocode.VideoCode import *

x = 700
y = 50


g = (
    group(
        # image("assets/icon.png").setPosition(0.5, 0.5),
        # video("assets/v.mp4").setPosition(0.5, 0.5),
        s := square(filled=True, cornerRadius=30, thickness=20).setPosition(x, y + 200),
        c := circle(filled=True, color=RED).setPosition(x, y + 500),
        r := rectangle(cornerRadius=0, thickness=8, color=GREEN).setPosition(x + 400, y + 350),
    )
    .apply(fadeIn())
    .add()
    .apply(
        moveTo(
            0.5,
            0.5,
        ),
    )
    .add()
)

# g.apply(scale(), start=2, duration=3).add()

# s.setAlign(x=LEFT)

for i in range(0, 50):
    g.apply(setPosition(y=0.5 + i / 100)).add()
    # s.width += 10
    # c.radius += 1
    # r.smth
```
