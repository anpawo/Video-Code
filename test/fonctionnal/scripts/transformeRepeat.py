from videocode.VideoCode import *

# text
t = text("a", 3).apply(repeat(24 * 2))
t.add()

# video
t = video("video/v.mp4").apply(repeat(2))
t.add()

# image
t = image("video/image.png").apply(repeat(24 * 2))
t.add()
