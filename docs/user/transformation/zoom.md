# Zoom Transformation

[go back to the transformations documentation](transformation.md)

The `zoom` transformation changes the scale of an input while keeping focus on a specific point. Unlike `scale`, zoom doesn't preserve content outside the original dimensions.

## Usage

To use the `zoom` transformation, create an instance of the `zoom` class with the desired factor and focal point coordinates.

### Arguments

- `factor` (float | int | tuple): Zoom factor(s) for x and y.
- `x` (float): Horizontal position of the zoom center (0.0 to 1.0, where 0.5 is the center).
- `y` (float): Vertical position of the zoom center (0.0 to 1.0, where 0.5 is the center).

### Example

```python
from videocode.VideoCode import *

# Create an image input
img = image("path/to/image.png")

# Apply the zoom transformation centered on the image
img.apply(zoom(factor=2, x=0.5, y=0.5))

# Apply zoom with focus on the top-left corner
img.apply(zoom(factor=1.5, x=0.25, y=0.25))

# Add the image to the timeline
img.add()
```
