from videocode.VideoCode import *

x = 700
y = 50

square(filled=True, cornerRadius=30, thickness=20).apply(translate(x, y + 175)).add().keep()
circle(filled=True, color=RED).apply(translate(x, y + 500)).add().keep()
rectangle(cornerRadius=0, thickness=8, color=GREEN).apply(translate(x + 300, y + 300)).add().keep()
