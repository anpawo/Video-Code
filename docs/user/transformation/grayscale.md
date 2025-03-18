# Grayscale Transformation

The `grayscale` transformation allows you to convert an input to grayscale.

## Usage

To use the `grayscale` transformation, you need to create an instance of the `grayscale` class.

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

## Definition

The `grayscale` transformation is defined in the following files:
- [videocode/transformation/color/Grayscale.py](../../../videocode/transformation/color/Grayscale.py)
- [src/transformation/color/grayscale.cpp](../../../src/transformation/color/grayscale.cpp)
