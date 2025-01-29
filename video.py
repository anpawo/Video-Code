from python.VideoCode import *

# copy first half then modify the original

v1 = video("video/v.mp4")

## v1.concat(v1)  # // TODO: last args should be a load not a string:  ['Call', 'concat', [['Call', 'load', ['v1']], 'v1']]

v2 = v1[0:60].copy()
v1.apply(grayscale())  # apply the filter to check if v2 stores a ref or the original
v2.concat(v2)

v1.add()
v2.add()
v1.add()

# copy first half then modify it
