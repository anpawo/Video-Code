
```py
from videocode.VideoCode import *

x = 700
y = 10

t = text("Hello", fontSize=3, duration=2).apply(translate(x, y + 175))
t.apply(fadeIn())
t.apply(fadeOut(), zoom(factor=(1, 3)))
t.add()

v = video("video/v.mp4").apply(translate(x, y + 175))
v.apply(zoom(factor=(1, 3)), endTime=1)
v.apply(zoom(factor=(3, 1)), startTime=1)
v.add()
v.keep()
```
