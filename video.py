from python.VideoCode import *

v1 = video("video/v.mp4")

v2 = v1[0:60].copy()

## grayscale video
## v1.apply(grayscale())  # apply the filter to check if v2 stores a ref or the original
## v1.add()

# fading in from left colored video
v2.apply(fade(LEFT))
v2.add()
