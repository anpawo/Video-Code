
```py
from videocode.VideoCode import *

x = 700
y = 10

# text: Video-Code
t = text("Video-Code", 3).apply(translate(x, y), repeat(24 * 4))
t[: 24 * 3].apply(fadeIn(LEFT))
t.add()
t.keep()

# text: Made by
t = text("made by", 3).apply(translate(x, y + 80), repeat(24 * 4))
t[: 24 * 3].apply(fadeIn(LEFT))
t.add()
t.keep()


# Me
v = video("video/v.mp4").apply(translate(x, y + 175))
v[0:20].apply(fadeIn())
v.add()
v.keep()
```
