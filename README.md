# Video-Code
The initial goal of this project is to create videos from code.<br>
I've always wanted to create millimetric videos and I will be able to, soon enough.

The second thought is that such thing can be used to automate the generation of video.<br>
AI have a hard time with designs, they are better with code, they could potentially take advantage of this project to generate videos with a good quality and a logical flow.

Thirdly, I want the program to have a visual interface like any other video editing app but I want it to be automatically generated from the Python API.<br>
With a code and a visual interface, anyone can make videos according to their liking.

Below is an example of the last feature added (code) and the result (video).



```py
from videocode.VideoCode import *

x = 700
y = 10

# text: Video-Code
t = text("Video-Code", 3).apply(translate(x, y), repeat(40))
t[:20].apply(fadeIn())
t.add()
t.keep()

# text: Made by
t = text("made by", 3).apply(translate(x, y + 80), repeat(40))
t[:20].apply(fadeIn())
t.add()
t.keep()


# Me
v = video("video/v.mp4").apply(translate(x, y + 175))
v[0:20].apply(fadeIn())
v.add()
v.keep()
```

<img src="docs/readme/example.gif" style="width: 50%;">

## Getting Started with Video-Code
To create a video with Video-Code, you need to write some simple code in Python.

The flow of the Video comes from the __Inputs__ that you, first import or create, then modify with __Transformations__ and finally add to the __timeline__.

To import or create an __Input__, you need to create a __video__, __image__ or a __text__ instance (soon shapes).<br>
To modify it, you need to use __Transformations__ like __translate__ or __fade__.<br>
To add the frames of the __Input__ to the timeline, use the __\<Input\>.add()__ function.

## Patch Notes


<details>
    <summary><code>Inputs</code></summary>
<br>

- `image`
- `video`
- `text`

</details>

<br>

<details>
    <summary><code>Transformations</code></summary>
<br>

- `fade`

<br>

- `translate`
- `move`

<br>

- `overlay`
- `repeat`

</details>

<br>

<details>
    <summary><code>Patchs</code></summary>
<br>

- `feature`: keep last frame of input on screen (06/03/25)
- `rework`: one stack (06/03/25)
- `transformation`: repeat (03/03/25)
- `input`: text (03/03/25)
- `rework`: position of the frames (02/03/25)
- `transformation`: move (02/03/25)

</details>

