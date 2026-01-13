
```py
#!/usr/bin/env python3


from videocode.videocode import *

# Display the same image three times: left lighter, center original, right darker
img_blur = image("../test.png").position(x=-4, y=0).scale(0.5).apply(grain(0.3), duration=2)

img_center = image("../test.png").position(x=0, y=0).scale(0.5)

img_gamma = image("../test.png").position(x=4, y=0).scale(0.5).apply(gamma(0.5), duration=2)
```
