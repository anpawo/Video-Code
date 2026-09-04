# Video-Code User Documentation

[go back to the main page](../../README.md)

## Overview

Video-Code is a project designed to create videos programmatically. It allows users to generate videos by writing code, providing precise control over video content and transformations. This project is ideal for creating millimetric videos, automating video generation, and integrating AI for video creation.

### Installation

1. **Clone the repository:**
    ```sh
    git clone git@github.com:anpawo/Video-Code.git
    cd Video-Code
    ```

    The directory is `Video-Code`, with the capitals. macOS does not care;
    Linux does, and `cd video-code` is where a tester on Linux stops.

2. **Install dependencies:**
    Ensure you have 'python3' and 'pip' installed. Then run:
    ```sh
    pip install -r requirements.txt
    ```

    Ensure you have `vcpkg` installed and set up in **manifest** mode. Then run:
    ```sh
    export VCPKG_ROOT="path/to/vcpkg"   # required, see below
    vcpkg install
    ```

    `VCPKG_ROOT` is not optional and not inferred: `CMakeLists.txt` stops at
    `VCPKG_ROOT environment variable not set` before it looks for anything
    else. Export it in your shell profile, not just in the terminal you build
    in.

3. **install qt6**

go to [qt6](https://www.qt.io/download) and download the latest version of qt6.
   - Select the components you need (e.g., Qt 6.x.x, CMake, etc.).
   - Follow the installation instructions.
   - Make sure to add the Qt installation path to your system's PATH environment variable.
   - Set the `Qt6_DIR` to the Qt installation path
   - For example:
     ```sh
     export Qt6_DIR="path/to/qt6/6.x.x/linux_gcc_64/lib/cmake/Qt6"
     ```

     Qt renamed that folder in 6.7: it is `linux_gcc_64` on recent versions and
     `gcc_64` on older ones. Look at what your install actually contains — the
     wrong one fails with `Could not find a package configuration file
     provided by "Qt6"`. On macOS it is `macos` instead.

4. **Build the project:**
    Ensure you have CMake installed. Then run:
    ```sh
    cmake -B build
    make -C build
    cp build/video-code video-code            # Linux
    ```

    On macOS the build produces an app bundle instead, and the binary lives
    inside it:

    ```sh
    cp build/video-code.app/Contents/MacOS/video-code video-code
    ```

    `make` from the repository root does the whole thing, including the copy
    for the right platform.

### Launch

To preview a scene in a bare window, run:
```sh
./video-code --file path/to/your/script.py
```
To open the editing shell — dock, timeline, properties and the scene's own
buffer — instead of the bare preview:
```sh
./video-code --file path/to/your/script.py --editor
```
If you want to generate a video directly, use:
```sh
./video-code --file path/to/your/script.py --generate out.mp4
```
Videos are 1920x1080 by default. Pass `-w`/`--width` and `--height` to change
it — the preview window and the rendered video both follow, and your script
needs no edit:
```sh
./video-code --file path/to/your/script.py -w 1200 --height 1500 --generate out.mp4
```
```sh
./video-code --file path/to/your/script.py --width 1200 --height 1500 --generate out.mp4
```

### Usage

To create a video with Video-Code, follow these steps:

1. **Create Inputs**: an input is a shape, a text, an image, a video or a sound — `Rectangle(...)`, `Text(...)`, `Image(...)`, `Video(...)`. Creating one puts it on screen: there is no separate "add" step.
2. **Transform them**: call methods on the input — `position`, `fadeIn`, `moveTo`, `scaleTo`, `apply(shader, duration=)` — each one an animation or a state written on the timeline.
3. **Let time pass**: `wait(n)` waits for every running animation, then holds the picture for `n` seconds.


## Principles

### Frame Rate
The project operates at a frame rate of 30 frames per second (fps). This means that each second of video consists of 30 individual frames.

### Timeline
The timeline is a sequence of frames that represent the video. Inputs such as images, videos, and text are added to the timeline, and transformations are applied to these inputs over time.

### Example

`docs/by-example/firstRectangle.py` is the smallest scene there is:

```python
from videocode import *

Rectangle(width=3, height=2, fillColor=BLUE_C, strokeColor=WHITE).fadeIn()

wait(1)
```

The same with a video, drawn at its natural size and turned grey:

```python
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

## Detailed Documentation

The complete map of what the API can do — every input, every transformation,
every effect, with the file it lives in and a runnable scene for each — is
[docs/FEATURES.md](../FEATURES.md). Longer worked examples live in
[docs/by-example/](../by-example/): `firstRectangle.py`, `layouts.py`,
`4_animations.py`, and the README's `tuto.py`.

## Conclusion

Video-Code provides a powerful way to create videos programmatically. By understanding the principles of inputs, transformations, and the timeline, you can create complex and precise video content. For more detailed information, refer to the feature map linked above.
