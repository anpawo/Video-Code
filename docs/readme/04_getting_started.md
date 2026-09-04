## Getting Started
To create a video with Video-Code, you need to write some simple code in Python.

An __Input__ is anything on screen — a shape, a text, an image, a video, a sound — and creating one puts it there: `Rectangle(...)`, `Text("...")`, `Image("x.png")`, `Video("x.mp4")`. There is no separate "add" step.<br>
To modify it, call its methods — `position`, `fadeIn`, `moveTo`, `scaleTo` — each one an animation written on the timeline.<br>
To let time pass, call `wait(n)`: it waits for every running animation, then holds the picture for `n` seconds.

The smallest scene there is, `docs/by-example/firstRectangle.py`:

```py
from videocode import *

Rectangle(width=3, height=2, fillColor=BLUE_C, strokeColor=WHITE).fadeIn()

wait(1)
```

Render it, or open it in the editing shell — dock, timeline, properties and the scene's own buffer, which re-runs as you type:

```sh
./video-code --file docs/by-example/firstRectangle.py --generate first.mp4
./video-code --file docs/by-example/firstRectangle.py --editor
```

A scene is a Python program, and opening one runs it — in the editor as much as
on the command line. Read a scene you did not write before you open it, the way
you would any script someone sent you.
