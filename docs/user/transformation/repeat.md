# Repeat Transformation

The `repeat` transformation allows you to repeat an input a specified number of frames.

## Usage

To use the `repeat` transformation, you need to create an instance of the `repeat` class by providing the number of repetitions.

### Arguments

- `n` (uint): The number of frames to repeat the input.

### Example

```python
from videocode.VideoCode import *

# Create a text input
txt = text("Hello, World!", fontSize=2, color=(255, 255, 255, 255))

# Apply the repeat transformation
txt.apply(repeat(5))

# Add the text to the timeline
txt.add()
```

## Definition

The `repeat` transformation is defined in the following files:
- [videocode/transformation/other/Repeat.py](../../../videocode/transformation/other/Repeat.py)
- [src/transformation/other/repeat.cpp](../../../src/transformation/other/repeat.cpp)
