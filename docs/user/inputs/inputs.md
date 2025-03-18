# Inputs

[go back to the user documentation](../user.md)

Inputs are the basic building blocks of your video project. They can be images, videos, or text that you import or create. Each input can be manipulated using various transformations.

## Available Inputs

- [Video](video.md)
- [Image](image.md)
- [Text](text.md)

## Usage

To use an input, you need to create an instance of the input class and then apply transformations to it. Finally, you add the input to the timeline.

### Example

```python
from videocode.VideoCode import *

# Create a video input
v = video("path/to/video.mp4")

# Add the video to the timeline
v.add()
```
