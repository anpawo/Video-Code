# Fade Transformation

[go back to the transformations documentation](transformation.md)

The `fade` transformation allows you to gradually change the opacity of an input over time.

## Usage

To use the `fade` transformation, you need to create an instance of the `fade` class by providing the sides to fade from, start and end opacity, and whether to affect transparent pixels.

### Arguments

- `sides` (list[side]): The sides to fade from, which can be `LEFT`, `RIGHT`, `TOP`, or `BOTTOM`.
- `startOpacity` (uint): The starting opacity.
- `endOpacity` (uint): The ending opacity.
- `affectTransparentPixel` (bool): Whether to affect transparent pixels.

### Example

```python
from videocode.VideoCode import *

# Create a text input
txt = text("Hello, World!", fontSize=2, color=(255, 255, 255, 255))

# Apply the fade transformation
txt.apply(fade(sides=LEFT, startOpacity=0, endOpacity=255))

# Add the text to the timeline
txt.add()
```

## Definition

The `fade` transformation is defined in the following files:
- [videocode/transformation/color/Fade.py](../../../videocode/transformation/color/Fade.py)
- [src/transformation/color/fade.cpp](../../../src/transformation/color/fade.cpp)
