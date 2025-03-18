from videocode.VideoCode import *

# text
t = text("a", 3).apply(repeat(24 * 2))
t[: 24].apply(move(0, 0, 100, 100))
t.add()

# video
t = video("video/v.mp4")
t[: 24].apply(move(0, 0, 100, 100))
t.add()

# image
t = image("video/image.png").apply(repeat(24 * 2))
t[: 24].apply(move(0, 0, 100, 100))
t.add()
