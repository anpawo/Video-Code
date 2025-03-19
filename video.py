from videocode.VideoCode import *

x = 700
y = 10

t = text("Hello", fontSize=3, duration=2).apply(translate(x, y))
t.apply(fadeIn(duration=1))
t.apply(fadeOut(duration=1))
t.add()

# text: Video-Code
t = text("Video-Code", fontSize=3, duration=2).apply(translate(x, y))
t.apply(fadeIn(sides=LEFT))
t.add()
t.keep()

# text: Made by
t = text("made by", fontSize=3, duration=2).apply(translate(x, y + 80))
t.apply(fadeIn(sides=LEFT))
t.add()
t.keep()



# Me
v = video("video/v.mp4").apply(translate(x, y + 175))
v.apply(zoomOut(4, (0.1,0.1)))
v.add()
v.keep()
