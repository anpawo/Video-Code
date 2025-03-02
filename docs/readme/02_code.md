
```py
from frontend.VideoCode import *


v1 = video("video/v.mp4")

v1[0:20].apply(fadeIn()).add()
v1[20:40].apply(fadeOut()).add()
```
