# Video-Code User Documentation

[go back to the main page](../../README.md)

## Overview

Video-Code is a project designed to create videos programmatically. It allows users to generate videos by writing code, providing precise control over video content and transformations. This project is ideal for creating millimetric videos, automating video generation, and integrating AI for video creation.

### Installation

1. **Clone the repository:**
    ```sh
    git clone git@github.com:anpawo/Video-Code.git
    cd video-code
    ```

2. **Install dependencies:**
    Ensure you have 'python3' and 'pip' installed. Then run:
    ```sh
    pip install -r requirements.txt
    ```

    Ensure you have `vcpkg` installed and set up in **manifest** mode. Then run:
    ```sh
    vcpkg install
    ```

3. **install qt6**

go to [qt6](https://www.qt.io/download) and download the latest version of qt6.
   - Select the components you need (e.g., Qt 6.x.x, CMake, etc.).
   - Follow the installation instructions.
   - Make sure to add the Qt installation path to your system's PATH environment variable.
   - Set the `Qt6_DIR` to the Qt installation path
   - For example:
     ```sh
     export Qt6_DIR="path/to/qt6/6.x.x/gcc_64/lib/cmake/Qt6"
     ```

4. **Build the project:**
    Ensure you have CMake installed. Then run:
    ```sh
    cmake -B build
    make -C build
    cp build/video-code video-code
    ```

### Launch

To launch the project, run:
```sh
./video-code --file path/to/your/script.py
```
If you want to generate a video directly, use:
```sh
./video-code --file path/to/your/script.py --generate

```

### Usage

To create a video with Video-Code, follow these steps:

1. **Import or Create Inputs**: Inputs can be images, videos, or text. These are the basic building blocks of your video.
2. **Apply Transformations**: Modify the inputs using various transformations such as translate, fade, overlay, etc.
3. **Add to Timeline**: Add the transformed inputs to the timeline to create the final video sequence.


## Principles

### Frame Rate
The project operates at a frame rate of 30 frames per second (fps). This means that each second of video consists of 30 individual frames.

### Timeline
The timeline is a sequence of frames that represent the video. Inputs such as images, videos, and text are added to the timeline, and transformations are applied to these inputs over time.

### Example

```python
from videocode.VideoCode import *

# Create a video input
v = video("path/to/video.mp4")

# Apply the grayscale transformation
v.apply(grayscale())

# Add the video to the timeline
v.add()
```

### methods

- `add()`: Adds the input to the timeline.

- `apply(transformation)`: Applies a transformation to the input. The transformation can be any of the available transformations such as `grayscale()`, `fade()`, etc.

- `keep()`: Keeps the last frame of the input on the timeline after the input ends.

## Detailed Documentation

For more detailed usage instructions, refer to the following user documentation:

- [Inputs](inputs/inputs.md)
  - [Video](inputs/video.md)
  - [Image](inputs/image.md)
  - [Text](inputs/text.md)
- [Transformations](transformation/transformation.md)
  - [Fade](transformation/fade.md)
  - [Grayscale](transformation/grayscale.md)
  - [Translate](transformation/translate.md)
  - [Move](transformation/move.md)
  - [Overlay](transformation/overlay.md)
  - [Repeat](transformation/repeat.md)
  - [Scale](transformation/scale.md)

## Conclusion

Video-Code provides a powerful way to create videos programmatically. By understanding the principles of inputs, transformations, and the timeline, you can create complex and precise video content. For more detailed information, refer to the linked user documentation sections.
