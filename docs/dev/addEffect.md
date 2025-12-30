# Adding a New Effect/Transformation

This document explains how to add a new effect/transformation to the Video-Code project. Transformations modify inputs over time, creating effects like movement, color changes, scaling, and more.

## Table of Contents

1. [Overview](#overview)
2. [Step 1: Define the Transformation in Python](#step-1-define-the-transformation-in-python)
3. [Step 2: Register the Python Transformation](#step-2-register-the-python-transformation)
4. [Step 3: Implement the Transformation in C++](#step-3-implement-the-transformation-in-c)
5. [Step 4: Register the C++ Transformation](#step-4-register-the-c-transformation)
6. [Step 5: Update Build Configuration](#step-5-update-build-configuration)
7. [Step 6: Testing](#step-6-testing)

## Overview

Transformations in Video-Code are effects that modify inputs over time. Follow these steps to add a new transformation.

## Step 1: Define the Transformation in Python

Create a new Python file in `videocode/transformation/your_category/`:

```python
# videocode/transformation/your_category/YourEffect.py

from videocode.transformation.Transformation import Transformation
from videocode.Constant import ufloat
from videocode.Checks import *

class yourEffect(Transformation):
    """
    Brief description of your transformation effect.
    
    Args:
        intensity: Effect intensity (0.0 to 1.0)
        param: Additional parameter
    """
    
    Checks = {
        "intensity": [isPositive, isFloat, isInRange(0, 1)],
        "param": [isPositive, isInt],
    }
    
    def __init__(self, intensity: ufloat = 1.0, param: int = 100) -> None:
        super().__init__()
        self.intensity = intensity
        self.param = param
```

## Step 2: Register the Python Transformation

Add to `videocode/transformation/_AllTransformation.py`:

```python
from videocode.transformation.your_category.YourEffect import *
```

## Step 3: Implement the Transformation in C++

Create `src/transformation/your_category/yourEffect.cpp`:

```cpp
#include "transformation/transformation.hpp"
#include <opencv2/opencv.hpp>

void transformation::yourEffect(std::shared_ptr<IInput> input, 
                               Register &reg, 
                               const json::object_t &args)
{
    float intensity = args.at("intensity").get<float>();
    int param = args.at("param").get<int>();
    
    cv::Mat frame = input->getFrame(reg.time);
    
    // Apply your effect to the frame
    // ... transformation logic ...
    
    input->setFrame(frame);
}
```

## Step 4: Register the C++ Transformation

Add to `include/transformation/transformation.hpp`:

```cpp
namespace transformation
{
    void yourEffect(std::shared_ptr<IInput> input, Register &reg, const json::object_t &args);
    
    static const std::map<std::string, 
        std::function<void(std::shared_ptr<IInput>, Register &, const json::object_t &)>> map{
        // ... existing transformations ...
        {"yourEffect", yourEffect},
    };
}
```

## Step 5: Update Build Configuration

Add to `CMakeLists.txt`:

```cmake
set(TRANSFORMATION_SOURCES
    # ... existing sources ...
    src/transformation/your_category/yourEffect.cpp
)
```

## Step 6: Testing

Test your transformation:

```python
from videocode.VideoCode import *

c = circle()
c.apply(yourEffect(intensity=0.8, param=150))
c.add()
```

Build and generate:

```bash
make cmake
./video-code --file test.py --generate output.mp4
```

## Additional Resources

For more details, see:
- [Main Developer Documentation](dev.md) - Architecture and internals
- [Contributing Guide](../../CONTRIBUTING.md) - Full contribution guidelines
- [Adding Inputs](addInput.md) - How to add new input types
- [Testing Guide](testing.md) - Testing procedures
- [Transformation Base Class](../../videocode/transformation/Transformation.py)
- [Existing Transformations](../../videocode/transformation/)
