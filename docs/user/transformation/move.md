# Move Transformation

[go back to the transformations documentation](transformation.md)

The `move` transformation allows you to move an input from its current position to a specified position over time.

## Usage

To use the `move` transformation, you need to create an instance of the `move` class by providing the destination coordinates.

### Arguments

- `x` (int): The destination x-coordinate.
- `y` (int): The destination y-coordinate.

### Example

```python
from videocode.VideoCode import *

# Create a video input
v = video("path/to/video.mp4")

# Apply the move transformation
v.apply(move(500, 300))

# Add the video to the timeline
v.add()
```

## Definition

The `move` transformation is defined in the following files:
- [videocode/transformation/position/Move.py](../../../videocode/transformation/position/Move.py)
- [src/transformation/position/move.cpp](../../../src/transformation/position/move.cpp)
