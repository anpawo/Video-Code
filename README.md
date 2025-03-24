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

square(filled=True, cornerRadius=30, thickness=20).apply(translate(x, y + 175)).add().keep()
circle(filled=True, color=RED).apply(translate(x, y + 500)).add().keep()
rectangle(cornerRadius=0, thickness=8, color=GREEN).apply(translate(x + 300, y + 300)).add().keep()
```

<img src="docs/readme/example.gif" style="width: 50%;">

## Getting Started
To create a video with Video-Code, you need to write some simple code in Python.

To create a video with Video-Code, you need to write some simple code in Python. The flow of the video comes from the **Inputs** that you first import or create, then modify with **Transformations**, and finally add to the **timeline**.

For more detailed usage instructions, refer to the [user documentation](docs/user/user.md).

### Installation

To install the project, checkout the [documentation](docs/user/user.md#installation).

## Patch Notes

To install the project, checkout the [documentation](docs/user/user.md#installation).

## Patch Notes

<details>
    <summary><code>Inputs</code></summary>
<br>

- `image`
- `video`

- `text`

- `circle`
- `rectangle`
- `square`

</details>

<br>

<details>
    <summary><code>Transformations</code></summary>
<br>

- `grayscale`
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

</details>
