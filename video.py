from videocode.VideoCode import *

x = 700
y = 10

t1 = text("Video-Code", fontSize=3, duration=2).apply(translate(x, y))
t1.apply(fadeIn(sides=LEFT), endTime=1)
t1.add()
t1.keep()

t = text("made by", fontSize=3, duration=2).apply(translate(x, y + 80))
t.apply(fadeIn(sides=LEFT), endTime=1)
t.apply(fadeOut(sides=RIGHT), startTime=1)
t.add()

t = text("Hippolyte and Marius", fontSize=3, duration=3).apply(translate(450, y + 80))
t.apply(fadeIn(sides=LEFT), endTime=1)
t.apply(fadeOut(sides=RIGHT), startTime=1)
t.add()

t = text("3 different inputs", fontSize=3, duration=4).apply(translate(x, y + 80))
t.apply(fadeIn(sides=LEFT), endTime=1)
t.apply(fadeOut(sides=RIGHT), startTime=1)
t.add()

t = text("text", fontSize=3, duration=2).apply(translate(x, y+ 200))
t.add()

# t = image("video/image.png").apply(translate(x, y+200))
# t.add()

# t = video("video/v.mp4").apply(translate(x, y+200))
# t.add()

t = text("6 different effects", fontSize=3, duration=2).apply(translate(x, y+80))
t.add()
t.keep()

t = text("fade", fontSize=3, duration=3).apply(translate(x, y + 500))
t.apply(fadeIn(sides=RIGHT), endTime=2)
t.apply(fadeOut(sides=RIGHT), startTime=2)
t.add()

t = text("zoom", fontSize=3, duration=4).apply(translate(x, y + 500))
t.apply(zoom(factor=(1,2), x=0.5, y=0.5), endTime=2)
t.apply(zoom(factor=(2,1), x=0.5, y=0.5), startTime=2)
t.add()

t = text("scale", fontSize=3, duration=4).apply(translate(x, y + 500))
t.apply(scale(factor=(1,2), centered=True), endTime=2)
t.apply(scale(factor=(2,1), centered=True), startTime=2)
t.add()

t = text("translate", fontSize=3, duration=4).apply(translate(x, y + 500))
t.apply(translate(x=0, y=100), startTime=1)
t.add()

t = text("move", fontSize=3, duration=4).apply(translate(x, y + 500))
t.apply(move(x=0, y=100), startTime=1)
t.add()

# t = video("video/v.mp4").apply(translate(x, y+200))
# t.apply(grayscale(), zoom(factor=(1,2), x=0.5, y=0.5), endTime=2)
# t.apply(zoom(factor=(2,1), x=0.5, y=0.5), startTime=2)
# t.add()
# t.keep()
