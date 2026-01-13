
```py
#!/usr/bin/env python3


from videocode.videocode import *

# Display the same image three times: left lower contrast, center original, right higher contrast
img_low_contrast = image("../test.png").position(x=-4, y=0).scale(0.5).apply(contrast(-80), duration=2)

img_center = image("../test.png").position(x=0, y=0).scale(0.5)

img_high_contrast = image("../test.png").position(x=4, y=0).scale(0.5).apply(contrast(80), duration=2)
```
