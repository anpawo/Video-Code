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
y = 50

# Set the automatic adder on because we only do one action at a time.
automaticAdderOn()

### ===> Creating shapes and setting their positions
g = (
    group(
        # image("assets/icon.png").setPosition(0.5, 0.5),
        # video("assets/v.mp4").setPosition(0.5, 0.5),
        c := circle(filled=True, color=RED).setPosition(x, y + 500),
        s := square(filled=True, cornerRadius=30, thickness=20).setPosition(x, y + 200),
        r := rectangle(cornerRadius=0, thickness=8, color=GREEN).setPosition(x + 400, y + 350),
    )
    # .apply(fadeIn())
    .apply(moveTo(0.5, 0.5))
)

# Set the automatic adder off because we do more than one action; we change the position and then augment the radius' size.
# We could join them both into one apply and keep the automatic adder.
automaticAdderOff()

### ===> Changing the circle and the rectangle
for i in range(0, 40):
    c.radius += 1
    r.width += 10
    r.height -= 2
    g.add()

# Separate
wait(0)

### ===> Changing the square
for i in range(0, 30):
    s.cornerRadius += 2
    s.add()
```

<img src="docs/readme/example.gif" style="width: 50%;">

## Getting Started
To create a video with Video-Code, you need to write some simple code in Python.

The flow of the Video comes from the __Inputs__ that you, first import or create, then modify with __Transformations__ and finally add to the __timeline__.

To import or create an __Input__, you need to create a __video__, __image__ or a __text__ instance (soon shapes).<br>
To modify it, you need to use __Transformations__ like __translate__ or __fade__.<br>
To add the frames of the __Input__ to the timeline, use the __\<Input\>.add()__ function.

### Installation

To install the project, checkout the [documentation](docs/user/user.md#installation).

## Patch Notes


<details open>
    <summary><code>Inputs</code></summary>
<br>

- `image`
- `video`

<br>

- `text`

<br>

- `circle`
- `rectangle`
- `square`

<br>

- `group`

</details>

<br>

<details open>
    <summary><code>Transformations</code></summary>
<br>

- `grayscale`
- `fadeIn / fadeOut`

<br>

- `moveTo`

<br>

- `scale`
- `zoom`

<br>

- `setPosition`

</details>

<br>

<details>
    <summary><code>Patchs</code></summary>
<br>

- `feature`: start and duration of transformation (08/04/25)
- `rework`: keeping (08/04/25)
- `feature`: wait -> freeze the screen for the duration (08/04/25)
- `transformation`: setPosition (08/04/25)
- `rework`: move -> moveTo (08/04/25)
- `input`: group (08/04/25)
- `input`: rectangle (24/03/25)
- `input`: circle (24/03/25)
- `transformation`: scale (20/03/25)
- `transformation`: zoom (19/03/25)
- `rework`: effects' duration (19/03/25)
- `transformation`: grayscale (19/03/25)
- `feature`: keep last frame of input on screen (06/03/25)
- `rework`: one stack (06/03/25)
- `transformation`: repeat (03/03/25)
- `input`: text (03/03/25)
- `rework`: position of the frames (02/03/25)
- `transformation`: move (02/03/25)
- `feature`: setters (update in real time the proportions of a shape) (20/09/25)
- `fix`: different framerate between the window and the generated video

</details>

