# Scale Transformation

[go back to the transformations documentation](transformation.md)

The `scale` transformation resizes an input by a factor. If the mode is set to "Center," the scaling is performed from the center of the input.

## Usage

To use the `scale` transformation, create an instance of the `scale` class with the desired factor and mode.

### Arguments

- `factor` (float | int | tuple): Scale factor(s) for x and y.
- `mode` (str): Either "Origin" or "Center".

### Example

```python
from videocode.VideoCode import *

# Create an image input
img = image("path/to/image.png")

# Apply the scale transformation
img.apply(scale(factor=2, mode="Center"))

# Add the image to the timeline
img.add()
```
