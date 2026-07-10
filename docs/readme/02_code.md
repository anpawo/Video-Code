
```py
#!/usr/bin/env python3

from videocode import *

BG = LinearGradient(rgba(10, 12, 20), rgba(30, 10, 18))

Text("Latest Feature", fontSize=0.3, fillColor=WHITE | 0.65).position(0, 3.2).fadeIn(duration=0.4)

title = Text("FIRE", fontSize=2.8, fillColor=fire(speed=2.2, quality=0.9)).position(0, 1.0)
title.fadeIn(duration=0.8)

bar = Rectangle(width=8.8, height=0.34, cornerRadius=20, fillColor=WHITE | 0.12).position(0, -1.35)
bar.apply(lightSweep(width=24, intensity=0.9, angle=18), duration=5.4)

caption = Text("shader fills + selective clock pausing", fontSize=0.22, fillColor=WHITE | 0.72).position(0, -2.2)
caption.fadeIn(duration=0.4)

phase1 = Text("wait(1.2)  ->  flames keep moving", fontSize=0.2, fillColor=WHITE).position(0, -3.0)
phase1.fadeIn(duration=0.25)
wait(1.2)

phase1.fadeOut(duration=0.2)
phase2 = Text("wait(1.2, stop=Clock.PAINTS)  ->  fire freezes, sweep keeps moving", fontSize=0.18, fillColor=WHITE).position(0, -3.0)
phase2.fadeIn(duration=0.2)
wait(1.2, stop=Clock.PAINTS)

phase2.fadeOut(duration=0.2)
phase3 = Text("freeze(1.2)  ->  paints and effects pause together", fontSize=0.18, fillColor=WHITE).position(0, -3.0)
phase3.fadeIn(duration=0.2)
freeze(1.2)

phase3.fadeOut(duration=0.3)
Text("fire(), silk(), starNest(), mathShader(...)", fontSize=0.2, fillColor=WHITE | 0.85).position(0, -3.0).fadeIn(duration=0.3)
wait(1.8)
```
