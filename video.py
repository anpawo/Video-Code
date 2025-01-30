from python.VideoCode import *

v1 = video("video/v.mp4")

## grayscale video
## v1.apply(grayscale())  # apply the filter to check if v2 stores a ref or the original
## v1.add()

# fading in from left colored video
v1.apply(fade(LEFT))
v1.add()
