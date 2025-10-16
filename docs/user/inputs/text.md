# Text Input

[go back to the inputs documentation](inputs.md)

The `text` input allows you to create text overlays in your project. This input can be manipulated using various transformations.

## Usage

To use the `text` input, you need to create an instance of the `text` class by providing the text string and optional formatting parameters.

### Arguments

- `s` (str): The text string.
- `fontSize` (float): The font size of the text.
- `color` (RGBA): The color of the text in RGBA format.
- `fontThickness` (int, optional): The thickness of the font.

### Example

```python
from videocode.VideoCode import *

# Create a text input
txt = text("Hello, World!", fontSize=2, color=(255, 255, 255, 255))

# Add the text to the timeline
txt.add()
```

## Definition

The `text` input is defined in the following files:
- [videocode/input/text/Text.py](../../../videocode/input/text/Text.py)
- [src/input/concrete/text/Text.cpp](../../../src/input/concrete/text/Text.cpp)
