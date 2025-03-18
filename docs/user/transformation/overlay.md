# Overlay Transformation

[go back to the transformations documentation](transformation.md)

The `overlay` transformation allows you to overlay one input on top of another.

## Usage

To use the `overlay` transformation, you need to create an instance of the `overlay` class by providing the foreground input.

### Arguments

- `fg` (Input): The foreground input to overlay.

### Example

```python
from videocode.VideoCode import *

# Create background and foreground inputs
bg = video("path/to/background.mp4")
fg = image("path/to/foreground.png")

# Apply the overlay transformation
bg.apply(overlay(fg))

# Add the background to the timeline
bg.add()
```

## Definition

The `overlay` transformation is defined in the following files:
- [videocode/transformation/other/Overlay.py](../../../videocode/transformation/other/Overlay.py)
- [src/transformation/other/overlay.cpp](../../../src/transformation/other/overlay.cpp)
