# Image Input

The `image` input allows you to import an image file into your project. This input can be manipulated using various transformations.

## Usage

To use the `image` input, you need to create an instance of the `image` class by providing the file path to the image.

### Arguments

- `filepath` (str): The path to the image file, supported formats include PNG, JPG, and GIF.

### Example

```python
from videocode.VideoCode import *

# Create an image input
img = image("path/to/image.png")

# Add the image to the timeline
img.add()
```

## Definition

The `image` input is defined in the following files:
- [videocode/input/media/Image.py](../../../videocode/input/media/Image.py)
- [src/input/concrete/media/Image.cpp](../../../src/input/concrete/media/Image.cpp)
