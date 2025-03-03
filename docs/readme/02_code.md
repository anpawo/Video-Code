
```py
from videocode.VideoCode import *

x = 700
y = 100

# text: Video-Code
t = text("Video-Code", 3).apply(translate(x, y), repeat(40))
t[:20].apply(fadeIn())
t[20:].apply(fadeOut())
t.add()

# text: Made by:
t = text("made by", 3).apply(translate(x, y), repeat(40))
t[:20].apply(fadeIn())
t[20:].apply(fadeOut())
t.add()


# Me
v = video("video/v.mp4").apply(translate(x, y + 100))
v[0:20].apply(fadeIn()).add()
v[20:40].apply(fadeOut()).add()
```
