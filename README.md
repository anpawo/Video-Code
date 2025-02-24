# Video-Code
The goal of this project is to create videos with code.

Below is an example of the last feature added (code) and the result (video).

```py
from frontend.VideoCode import *


v1 = video("video/v.mp4")

v1[:20].apply(fadeIn())
v1[-20:].apply(fadeOut())

v1.add()
```

<img src="docs/readme/example.gif" style="width: 50%;">
