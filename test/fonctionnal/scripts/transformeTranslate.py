from videocode.VideoCode import *

# text
t = text("a", 3).apply(translate(0, 0, 100, 100))
t.add()

# video
t = video("video/v.mp4").apply(translate(0, 0, 100, 100))
t.add()

# image
t = image("video/image.png").apply(translate(0, 0, 100, 100))
t.add()
