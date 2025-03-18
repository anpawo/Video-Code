# Video-Code User Documentation

[go back to the main page](../README.md)

## Overview

Video-Code is a project designed to create videos programmatically. It allows users to generate videos by writing code, providing precise control over video content and transformations. This project is ideal for creating millimetric videos, automating video generation, and integrating AI for video creation.

## Principles

### Frame Rate
The project operates at a frame rate of 24 frames per second (fps). This means that each second of video consists of 24 individual frames.

### Timeline
The timeline is a sequence of frames that represent the video. Inputs such as images, videos, and text are added to the timeline, and transformations are applied to these inputs over time.

## Usage

To create a video with Video-Code, follow these steps:

1. **Import or Create Inputs**: Inputs can be images, videos, or text. These are the basic building blocks of your video.
2. **Apply Transformations**: Modify the inputs using various transformations such as translate, fade, overlay, etc.
3. **Add to Timeline**: Add the transformed inputs to the timeline to create the final video sequence.

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

## Conclusion

Video-Code provides a powerful way to create videos programmatically. By understanding the principles of inputs, transformations, and the timeline, you can create complex and precise video content. For more detailed information, refer to the linked user documentation sections.
