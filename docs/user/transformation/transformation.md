# Transformations

[go back to the user documentation](../user.md)

Transformations allow you to manipulate inputs in various ways. They can change the position, color, or other properties of an input over time.

## Available Transformations

- [Fade](fade.md)
- [Grayscale](grayscale.md)
- [Translate](translate.md)
- [Move](move.md)
- [Overlay](overlay.md)
- [Repeat](repeat.md)

## Usage

To use a transformation, you need to create an instance of the transformation class and then apply it to an input.

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
