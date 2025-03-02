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


v1 = video("video/v.mp4")


v1[0:40].apply(move(200, 0))
v1[0:20].apply(fadeIn()).add()
v1[20:40].apply(fadeOut()).add()
```

<img src="docs/readme/example.gif" style="width: 50%;">

## Getting Started with Video-Code
To create a video with Video-Code, you need to write some simple code in Python.

The flow of the Video comes from the __Inputs__ that you, first import or create, then modify with __Transformations__ and finally add to the __timeline__.

To import or create an __Input__, you need to create a __video__ or __image__ instance (soon text and shapes).<br>
To modify it, you need to use __Transformations__ like __translate__ or __fade__.<br>
To add the frames of the __Input__ to the timeline, use the __\<Input\>.add()__ function.

## Patch Notes


<details open>
    <summary><code>Inputs</code></summary>
<br>

- `image`
- `video`

</details>

<br>

<details open>
    <summary><code>Transformations</code></summary>
<br>

- `fade`

<br>

- `translate`
- `move`

<br>

- `overlay`

</details>

<br>

<details open>
    <summary><code>Patchs</code></summary>
<br>

- `rework`: position of the frames (02/03/25)
- `transformation`: move (02/03/25)

</details>

