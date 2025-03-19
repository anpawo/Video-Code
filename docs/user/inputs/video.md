# Video Input

[go back to the inputs documentation](inputs.md)

The `video` input allows you to import a video file into your project. This input can be manipulated using various transformations.

## Usage

To use the `video` input, you need to create an instance of the `video` class by providing the file path to the video.

### Arguments

- `filepath` (str): The path to the video file, supported formats include MP4, AVI, and MKV.

### Example

```python
from videocode.VideoCode import *

# Create a video input
v = video("path/to/video.mp4")

# Add the video to the timeline
v.add()
```

## Definition

The `video` input is defined in the following files:
- [videocode/input/media/Video.py](../../../videocode/input/media/Video.py)
- [src/input/concrete/media/Video.cpp](../../../src/input/concrete/media/Video.cpp)
