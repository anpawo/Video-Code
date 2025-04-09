
```py
from videocode.VideoCode import *

x = 700
y = 50

g = (
    group(
        # image("assets/icon.png").setPosition(0.5, 0.5),
        # video("assets/v.mp4").setPosition(0.5, 0.5),
        square(filled=True, cornerRadius=30, thickness=20).setPosition(x, y + 200),
        circle(filled=True, color=RED).setPosition(x, y + 500),
        rectangle(cornerRadius=0, thickness=8, color=GREEN).setPosition(x + 400, y + 350),
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

g.apply(scale(), start=2, duration=3).add()
```
