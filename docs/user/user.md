# Building and running Video-Code

[← back to the README](../../README.md)

A scene is a Python file. Every shape, text, image and clip in it is a line of
code, every movement a method call on that line, so a picture can be exact to
the pixel, produced by a program, or written by an AI that is better at code
than at design. The same scene opens in an editor whose panels are generated
from the Python API. This page is the build from source; the
[prebuilt release](../../README.md#installation) needs none of it.

### Building from source

1. **Get the sources**
    ```bash
    git clone https://github.com/anpawo/Video-Code.git
    cd Video-Code
    ```

    The directory is `Video-Code`, with the capitals. macOS does not care;
    Linux does, and `cd video-code` is where a tester on Linux stops.

2. **Python packages, and vcpkg**
    Python 3.12 or newer, and its `pip`:
    ```bash
    python3 -m pip install pybind11 -r requirements.txt
    ```

    The C++ dependencies — Qt 6, OpenCV, FFmpeg, Vulkan, FreeType — are built
    by vcpkg from the manifest in this repository, at the first build, which
    takes an hour or more. vcpkg only has to be checked out and named:
    ```bash
    export VCPKG_ROOT="path/to/vcpkg"   # required, see below
    ```

    `VCPKG_ROOT` is not optional and not inferred: `make` passes vcpkg's
    toolchain file to CMake from it, and with the variable unset the configure
    stops at once on `Could not find toolchain file: /scripts/buildsystems/vcpkg.cmake`.
    Export it in your shell profile, not just in the terminal you build in.

3. **Build**
    CMake 3.25 or newer and Ninja, then from the repository root:
    ```bash
    make
    ```

    `make` from the repository root does the whole thing, including the copy
    for the right platform: on Linux the binary is `build/video-code`, and on
    macOS the build produces an app bundle instead, and the binary lives
    inside it:

    ```bash
    cp build/video-code.app/Contents/MacOS/video-code video-code
    ```

    On Linux, [docs/SETUP_LINUX.md](../SETUP_LINUX.md) has the system packages
    to install first and the flags `make` does not know about.

### Running a scene

To preview a scene in a bare window, run:
```bash
./video-code --file path/to/your/script.py
```
To open the editing shell — dock, timeline, properties and the scene's own
buffer — instead of the bare preview:
```bash
./video-code --file path/to/your/script.py --editor
```
To render the video file straight away:
```bash
./video-code --file path/to/your/script.py --generate out.mp4
```
Videos are 1920x1080 by default. Pass `-w`/`--width` and `--height` to change
it — the preview window and the rendered video both follow, and your script
needs no edit:
```bash
./video-code --file path/to/your/script.py -w 1200 --height 1500 --generate out.mp4
```
```bash
./video-code --file path/to/your/script.py --width 1200 --height 1500 --generate out.mp4
```

### Writing a scene

Three verbs make a scene:

1. **Create Inputs**: an input is a shape, a text, an image, a video or a sound — `Rectangle(...)`, `Text(...)`, `Image(...)`, `Video(...)`. Creating one puts it on screen: there is no separate "add" step.
2. **Transform them**: call methods on the input — `position`, `fadeIn`, `moveTo`, `scaleTo`, `apply(shader, duration=)` — each one an animation or a state written on the timeline.
3. **Let time pass**: `wait(n)` waits for every running animation, then holds the picture for `n` seconds.

## How time works

### Frames
The project operates at a frame rate of 30 frames per second (fps). This means that each second of video consists of 30 individual frames.

### The timeline
Everything a scene writes lands on one timeline, in the order the lines run: an
input appears when its line executes, an animation occupies the frames between
its start and its end, and `wait(n)` moves the clock forward. Nothing is placed
by hand; the code is the placement.

### Two scenes

`docs/by-example/firstRectangle.py` is the smallest scene there is:

```py
from videocode import *

Rectangle(width=3, height=2, fillColor=BLUE_C, strokeColor=WHITE).fadeIn()

wait(1)
```

The same with a video, drawn at its natural size and turned grey:

```py
from videocode import *

clip = Video("path/to/video.mp4").position(x=0, y=0)
clip.apply(grayscale(), duration=1)

wait(1)
```

Both render with `./video-code --file <scene.py> --generate out.mp4`.

### Methods

Every input shares the same methods (`videocode/input/input.py`). The ones a
first scene needs:

- `position(x, y)`: place the input — world units, one unit is 120 px, `(0, 0)` is the centre of the frame, Y is up.
- `apply(shader, duration=n)`: run a fragment shader on the input for `n` seconds — `grayscale()`, `blur(5)`, `lightSweep()`, etc. Without `duration` it lasts one frame.
- `fadeIn()` / `fadeOut()`: animate the opacity, 0.4 s by default.
- `moveTo(x, y)` / `moveBy(x, y)` / `scaleTo(factor)` / `rotateBy(degrees)`: smooth animations, `duration=` and `easing=` on each.
- `wait(n)`: not a method — a free function that waits for every animation and then holds `n` seconds.

## Where the rest is

The complete map of what the API can do — every input, every transformation,
every effect, with the file it lives in and a runnable scene for each — is
[docs/FEATURES.md](../FEATURES.md). Longer worked examples live in
[docs/by-example/](../by-example/): `firstRectangle.py`, `layouts.py`,
`4_animations.py`, and the README's `tuto.py`.

## In short

Video-Code provides a powerful way to create videos programmatically. By understanding the principles of inputs, transformations, and the timeline, you can create complex and precise video content. For more detailed information, refer to the feature map linked above.
