
```py
from frontend.VideoCode import *


v1 = video("video/v.mp4")

v1[:20].apply(fadeIn())
v1[-20:].apply(fadeOut())

v1.add()
```
