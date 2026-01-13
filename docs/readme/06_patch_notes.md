## Patch Notes


<details open>
    <summary><code>Inputs</code></summary>
<br>

- `image`
- `video`
- `webImage`

<br>

- `circle`
- `rectangle`
- `square`
- `line`

<br>

- `text`

<br>

- `group`

</details>

<br>

<details open>
    <summary><code>Transformations</code></summary>
<br>


- `position`
- `align`
- `rotate`
- `scale`
- `args`
- `hide`
- `show`

</details>

<br>

<details open>
    <summary><code>Shaders</code></summary>
<br>

- `grayscale`
- `opacity`
- `blur`
- `gamma`
- `grain`
- `brightness`
- `contrast`

</details>

<br>

<details open>
    <summary><code>Effect Templates</code></summary>
<br>

- `moveTo`
- `moveBy`

<br>

- `scaleTo`
- `scaleBy`

<br>

- `fadeIn`
- `fadeOut`

</details>

<br>

<details>
    <summary><code>Patchs</code></summary>
<br>

- `feature`: start and duration of transformation (08/04/25)
- `rework`: inputs are kept on the video by default (08/04/25)
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
- `feature`: image from url
- `rework`: moveTo
- `rework`: scale
- `feature`: persistent transformations
- `input`: line (01/01/2026)
- `transformation`: align, args, hide, position, rotate, scale, show => basic transformation (01/01/2026)
- `template`: moveTo, moveBy, scaleTo, scaleBy, fadeIn, fadeOut => effect overtime that are smooth (01/01/2026)
- `feature`: flush => prevents effects to be applied at the same time (01/01/2026)
- `feature`: frames are not kept in memory anymore, they are generated on the fly. (01/01/2026)

</details>
