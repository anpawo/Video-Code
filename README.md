# Video-Code
The initial goal of this project is to create videos from code.<br>
I've always wanted to create millimetric videos and I will be able to, soon enough.

The second thought is that such thing can be used to automate the generation of video.<br>
AI have a hard time with designs, they are better with code, they could potentially take advantage of this project to generate videos with a good quality and a logical flow.

Thirdly, I want the program to have a visual interface like any other video editing app but I want it to be automatically generated from the Python API.<br>
With a code and a visual interface, anyone can make videos according to their liking.

Below is an example of the last feature added (code) and the result (video).



```py
#!/usr/bin/env python3


from videocode.VideoCode import *
from videocode.template.league.runes import *

r = RuneSet(
    main=(
        Path.Precision,
        Rune.LethalTempo,
        Rune.Triumph,
        Rune.LegendAlacrity,
        Rune.LastStand,
    ),
    sub=(
        Path.Resolve,
        Rune.BonePlating,
        Rune.ShieldBash,
    ),
    shard=(
        Shard.AdaptativeForce,
        Shard.AttackSpeed,
        Shard.HealthScaling,
    ),
).animate()

wait(1)
```

<img src="docs/readme/example.gif" style="width: 50%;">

## Getting Started
To create a video with Video-Code, you need to write some simple code in Python.

The flow of the Video comes from the __Inputs__ that you, first import or create, then modify with __Transformations__ and finally add to the __timeline__.

To import or create an __Input__, you need to create a __video__, __image__ or a __text__, etc...<br>
To modify it, you need to use __Transformations__ like __translate__ or __fade__.<br>
To add the frames of the __Input__ to the timeline, use the __\<Input\>.add()__ function.

### Installation

To install the project, checkout the [documentation](docs/user/user.md#installation).

## Patch Notes


<details open>
    <summary><code>Inputs</code></summary>
<br>

- `local image`
- `local video`
- `web image`

<br>

- `text`

<br>

- `circle`
- `rectangle`
- `square`

<br>

- `group`
- `incremental`

</details>

<br>

<details open>
    <summary><code>Transformations</code></summary>
<br>

- `grayscale`
- `fadeIn / fadeOut`

<br>

- `moveTo`
- `slideTo`

<br>

- `scale`
- `zoom`

<br>

- `setPosition`
- `setArgument`

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
- `feature`: incrementals: groups that alterate the modifications you receive according to you're index
- `feature`: image from url
- `feature`: first template example (runeset)

</details>

