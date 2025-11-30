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
- `feature`: incrementals: groups that alterate the modifications you receive according to you're index
- `feature`: image from url
- `feature`: first template example (runeset)
- `rework`: slideTo becomes moveTo and the old moveTo is removed
- `feature`: can apply transformations to the whole scene
- `rework`: scale removed and zoom renamed scale
- `feature`: persistent transformations: you trigger once grayscale and it stays with the input forever

</details>
