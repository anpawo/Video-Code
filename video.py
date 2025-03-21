from videocode.VideoCode import *

x = 700
y = 10

t = text("Video-Code", fontSize=3, duration=2).apply(translate(x, y))
t.apply(fadeIn(sides=LEFT), endTime=1)
t.apply(fadeOut(sides=RIGHT), startTime=1)
t.add()

t = text("made by", fontSize=3, duration=2).apply(translate(x, y))
t.apply(fadeIn(sides=LEFT), endTime=1)
t.apply(fadeOut(sides=RIGHT), startTime=1)
t.add()

t = text("Hippolyte and Marius", fontSize=3, duration=2).apply(translate(450, y))
t.apply(fadeIn(sides=LEFT), endTime=1)
t.apply(fadeOut(sides=RIGHT), startTime=1)
t.add()

t = text("3 different inputs", fontSize=3, duration=2).apply(translate(450, y))
t.apply(fadeIn(sides=LEFT), endTime=1)
t.apply(fadeOut(sides=RIGHT), startTime=1)
t.add()

t = text("text", fontSize=3, duration=2).apply(translate(x, y- 200))
t.add()

t = image("video/image.png").apply(translate(x, y-200))
t.add()

t = video("video/v.mp4").apply(translate(x, y-200))
t.add()

t = text("6 different effects", fontSize=3, duration=2).apply(translate(x, y))
t.add()

t = image("video/image.png").apply(translate(x, y))
t.apply(fadeIn(sides=LEFT), endTime=1)
t.apply(fadeOut(sides=RIGHT), startTime=1)
t.add()

t = video("video/v.mp4").apply(translate(x, y))
t.apply(grayscale(), move(x=0, y=0), endTime=1)
t.apply(zoom(factor=(1, 3)), startTime=1, endTime=3)
t.apply(zoom(factor=(3, 1)), startTime=3, endTime=6)
t.apply(scale(factor=(1, 3)), startTime=6, endTime=7)
t.apply(zoom(factor=(3, 1)), startTime=7)
t.add()
