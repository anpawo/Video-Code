# Translate Transformation

The `translate` transformation allows you to move an input from one position to another by specifying the x and y offsets.

## Usage

To use the `translate` transformation, you need to create an instance of the `translate` class by providing the x and y offsets.

### Arguments

- `dx` (int): The offset in the x-direction.
- `dy` (int): The offset in the y-direction.

### Example

```python
from videocode.VideoCode import *

# Create an image input
img = image("path/to/image.png")

# Apply the translate transformation
img.apply(translate(dx=100, dy=50))

# Add the image to the timeline
img.add()
```

## Definition

The `translate` transformation is defined in the following files:
- [videocode/transformation/position/Translate.py](../../../videocode/transformation/position/Translate.py)
- [src/transformation/position/translate.cpp](../../../src/transformation/position/translate.cpp)
