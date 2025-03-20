from videocode.VideoCode import *

x = 700
y = 10

t = text("Hello", fontSize=3, duration=2).apply(translate(x, y + 175))
t.apply(fadeIn())
t.apply(fadeOut(), zoom(factor=(1, 3)))
t.add()

v = video("video/v.mp4").apply(translate(x, y + 175))
v.apply(scale(factor=(1, 0.2), mode="Center"), endTime=2)
v.apply(scale(factor=(0.2, 1), mode="Center"), startTime=2)
v.add()
v.keep()
