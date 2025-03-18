from videocode.VideoCode import *

# text
t = text("a", 3).apply(repeat(24 * 2))
t[: 24].apply(fadeIn(LEFT))
t.add()

# text
t = text("b", 3).apply(repeat(24 * 2))
t[: 24].apply(fadeIn(RIGHT))
t.add()

# video
t = video("video/v.mp4")
t[: 24].apply(fadeIn(UP))
t.add()

# video
t = video("video/v.mp4")
t[: 24].apply(fadeIn(DOWN))
t.add()

# image
t = image("video/image.png").apply(repeat(24 * 2))
t[: 24].apply(fade(UP, 50, 75, True))
t.add()

# image
t = image("video/image.png").apply(repeat(24 * 2))
t[: 24].apply(fade(UP, 75, 50, False))
t.add()
