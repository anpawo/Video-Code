# Adding a New Input Type

This document explains how to add a new input type to the Video-Code project. Inputs are the building blocks of videos (images, videos, shapes, text, etc.).

## Table of Contents

1. [Overview](#overview)
2. [Step 1: Define the Input in Python](#step-1-define-the-input-in-python)
3. [Step 2: Register the Python Input](#step-2-register-the-python-input)
4. [Step 3: Implement the Input in C++](#step-3-implement-the-input-in-c)
5. [Step 4: Register the C++ Input](#step-4-register-the-c-input)
6. [Step 5: Update Build Configuration](#step-5-update-build-configuration)
7. [Step 6: Testing](#step-6-testing)
8. [Examples](#examples)

## Overview

Adding a new input type requires parallel implementation in both Python and C++:

1. **Python API**: User-facing class with parameters and methods
2. **C++ Runtime**: Frame generation and rendering logic
3. **Serialization**: JSON bridge between layers
4. **Registration**: Make the input discoverable to the system

## Step 1: Define the Input in Python

Create a new Python file in the appropriate category under `videocode/input/`:

### File Structure

```
videocode/input/
├── media/          # Images, videos
├── shape/          # Geometric shapes
├── text/           # Text and formulas
├── group/          # Input groups
├── camera/         # Camera input
└── your_category/  # Your new category (if needed)
```

### Basic Template

```python
# videocode/input/your_category/YourInput.py

from videocode.input.Input import Input
from videocode.Decorators import inputCreation
from videocode.Constant import uint, rgba, RED
from videocode.Checks import *

class yourInput(Input):
    """
    Brief description of your input.
    
    Args:
        param1: Description of parameter 1
        param2: Description of parameter 2
        color: RGBA color tuple (default: RED)
    """
    
    Checks = {
        "param1": [isPositive, isInt],
        "param2": [isPositive, isInt],
        "color": [isRGBA],
    }
    
    @inputCreation
    def __init__(self, 
                 param1: uint = 100, 
                 param2: uint = 50,
                 color: rgba = RED) -> None:
        # The @inputCreation decorator handles:
        # 1. Type validation using Checks dict
        # 2. Serialization to Global.stack
        # 3. Attribute assignment
        pass
```

### Key Concepts

**The @inputCreation Decorator**:
- Automatically validates parameters against `Checks` dictionary
- Serializes creation action to `Global.stack` as JSON
- Assigns all parameters as instance attributes
- Generates unique input ID

**Type Hints**:
Use custom types from `Constant.py`:
- `uint`: Unsigned integer
- `ufloat`: Unsigned float
- `rgba`: Color tuple (R, G, B, A) with 0-255 values
- `sec`, `t`: Time values
- `default(value)`: Optional parameter with fallback

**Validation**:
Define `Checks` dictionary with validators from `Checks.py`:
- `isPositive`: Value must be positive
- `isInt`, `isFloat`: Type checks
- `isRGBA`: Valid RGBA tuple
- `isInRange(min, max)`: Range validation

### Example: Creating a Triangle Input

```python
# videocode/input/shape/Triangle.py

from videocode.input.Input import Input
from videocode.Decorators import inputCreation
from videocode.Constant import uint, rgba, RED
from videocode.Checks import *

class triangle(Input):
    """
    Creates a triangle shape.
    
    Args:
        base: Width of the triangle base in pixels
        height: Height of the triangle in pixels
        color: RGBA color (default: RED)
    """
    
    Checks = {
        "base": [isPositive, isInt],
        "height": [isPositive, isInt],
        "color": [isRGBA],
    }
    
    @inputCreation
    def __init__(self, 
                 base: uint = 100, 
                 height: uint = 100,
                 color: rgba = RED) -> None:
        pass
```

## Step 2: Register the Python Input

### Update Category Export

If creating a new category, create `_YourCategory.py`:

```python
# videocode/input/your_category/_YourCategory.py

from videocode.input.Input import Input

class YourCategory(Input):
    """Base class for your category inputs."""
    pass
```

### Update _AllInput.py

Add your input to the main export file:

```python
# videocode/input/_AllInput.py

# Existing imports...
from videocode.input.media.Image import *
from videocode.input.media.Video import *

# Add your import
from videocode.input.your_category.YourInput import *
```

### Make Input Accessible

Ensure your input is exported in `VideoCode.py`:

```python
# videocode/VideoCode.py

# The _AllInput import should make it automatically available
from videocode.input._AllInput import *
```

## Step 3: Implement the Input in C++

Create corresponding C++ files in `src/input/` and `include/input/`.

### Header File

```cpp
// include/input/your_category/YourInput.hpp

#pragma once

#include "input/IInput.hpp"
#include <opencv2/opencv.hpp>
#include <nlohmann/json.hpp>

using json = nlohmann::json;

namespace input
{
    class YourInput : public IInput
    {
    private:
        int param1;
        int param2;
        cv::Scalar color;
        
    public:
        // Constructor from JSON arguments
        YourInput(const json::object_t &args);
        
        // Generate frame at given time
        cv::Mat getFrame(int time) override;
        
        // Get total duration in frames
        int getDuration() const override;
        
        // Copy input
        std::shared_ptr<IInput> copy() const override;
    };
}
```

### Implementation File

```cpp
// src/input/your_category/YourInput.cpp

#include "input/your_category/YourInput.hpp"
#include <iostream>

namespace input
{
    YourInput::YourInput(const json::object_t &args)
    {
        // Extract parameters from JSON
        param1 = args.at("param1").get<int>();
        param2 = args.at("param2").get<int>();
        
        // Extract RGBA color
        auto colorArray = args.at("color").get<std::vector<int>>();
        color = cv::Scalar(colorArray[0], colorArray[1], 
                          colorArray[2], colorArray[3]);
    }
    
    cv::Mat YourInput::getFrame(int time)
    {
        // Create frame based on global dimensions
        cv::Mat frame = cv::Mat::zeros(Global::HEIGHT, Global::WIDTH, CV_8UC4);
        
        // Draw your input (example: filled rectangle)
        cv::Rect rect(
            (Global::WIDTH - param1) / 2,   // Center X
            (Global::HEIGHT - param2) / 2,  // Center Y
            param1,                          // Width
            param2                           // Height
        );
        cv::rectangle(frame, rect, color, cv::FILLED);
        
        return frame;
    }
    
    int YourInput::getDuration() const
    {
        // Return 1 frame for static inputs
        // For animated inputs, return actual duration
        return 1;
    }
    
    std::shared_ptr<IInput> YourInput::copy() const
    {
        return std::make_shared<YourInput>(*this);
    }
}
```

### Triangle Example

```cpp
// include/input/shape/Triangle.hpp

#pragma once

#include "input/IInput.hpp"
#include <opencv2/opencv.hpp>

namespace input
{
    class Triangle : public IInput
    {
    private:
        int base;
        int height;
        cv::Scalar color;
        
    public:
        Triangle(const json::object_t &args);
        cv::Mat getFrame(int time) override;
        int getDuration() const override;
        std::shared_ptr<IInput> copy() const override;
    };
}
```

```cpp
// src/input/shape/Triangle.cpp

#include "input/shape/Triangle.hpp"

namespace input
{
    Triangle::Triangle(const json::object_t &args)
    {
        base = args.at("base").get<int>();
        height = args.at("height").get<int>();
        
        auto colorArray = args.at("color").get<std::vector<int>>();
        color = cv::Scalar(colorArray[0], colorArray[1], 
                          colorArray[2], colorArray[3]);
    }
    
    cv::Mat Triangle::getFrame(int time)
    {
        cv::Mat frame = cv::Mat::zeros(Global::HEIGHT, Global::WIDTH, CV_8UC4);
        
        // Calculate triangle points
        int centerX = Global::WIDTH / 2;
        int centerY = Global::HEIGHT / 2;
        
        std::vector<cv::Point> points = {
            cv::Point(centerX, centerY - height / 2),        // Top
            cv::Point(centerX - base / 2, centerY + height / 2),  // Bottom left
            cv::Point(centerX + base / 2, centerY + height / 2)   // Bottom right
        };
        
        // Draw filled triangle
        cv::fillConvexPoly(frame, points, color);
        
        return frame;
    }
    
    int Triangle::getDuration() const
    {
        return 1;
    }
    
    std::shared_ptr<IInput> Triangle::copy() const
    {
        return std::make_shared<Triangle>(*this);
    }
}
```

## Step 4: Register the C++ Input

### Update Input Factory

Inputs are created through a factory pattern in `Core.cpp`. Register your input:

```cpp
// src/core/Core.cpp

#include "input/your_category/YourInput.hpp"

// In the input creation section:
std::shared_ptr<IInput> createInput(const std::string &type, const json::object_t &args)
{
    if (type == "YourInput") {
        return std::make_shared<input::YourInput>(args);
    }
    // ... other input types ...
}
```

### Alternative: Input Map Pattern

Some implementations use a map-based approach:

```cpp
// include/input/input.hpp

namespace input
{
    std::shared_ptr<IInput> createYourInput(const json::object_t &args);
    
    static const std::map<std::string, 
                         std::function<std::shared_ptr<IInput>(const json::object_t&)>> inputMap = {
        {"Circle", createCircle},
        {"Rectangle", createRectangle},
        {"YourInput", createYourInput},  // Add here
        // ... other inputs ...
    };
}
```

## Step 5: Update Build Configuration

### Add to CMakeLists.txt

```cmake
# CMakeLists.txt

# Find the input sources section and add:
set(INPUT_SOURCES
    # Existing sources...
    src/input/media/Image.cpp
    src/input/media/Video.cpp
    
    # Add your input
    src/input/your_category/YourInput.cpp
)
```

### Rebuild Project

```bash
make cmake
# or
cmake --build build
```

## Step 6: Testing

### Python Test

Create a test script:

```python
# tests/python/test_your_input.py

import sys
sys.path.append('./videocode')

from videocode.VideoCode import *

def test_your_input_creation():
    """Test creating your input."""
    inp = yourInput(param1=100, param2=50)
    assert inp.param1 == 100
    assert inp.param2 == 50
    
def test_your_input_in_video():
    """Test your input in a video."""
    inp = yourInput(param1=200, param2=100, color=BLUE)
    inp.add()
    
    # Verify it was added to stack
    from videocode.Global import stack
    assert len(stack) > 0
    assert stack[-1]["type"] == "YourInput"

if __name__ == "__main__":
    test_your_input_creation()
    test_your_input_in_video()
    print("All tests passed!")
```

### Manual Test

```python
# test_manual.py

from videocode.VideoCode import *

# Create your input
inp = yourInput(param1=300, param2=200, color=GREEN)
inp.add()

# Test with transformations
inp.apply(scale(2)).add()
inp.setPosition(100, 100).add()
```

### C++ Test

```cpp
// tests/cpp/test_your_input.cpp

#include <gtest/gtest.h>
#include "input/your_category/YourInput.hpp"

TEST(YourInputTest, Creation) {
    json::object_t args = {
        {"param1", 100},
        {"param2", 50},
        {"color", std::vector<int>{255, 0, 0, 255}}
    };
    
    auto input = std::make_shared<input::YourInput>(args);
    ASSERT_NE(input, nullptr);
}

TEST(YourInputTest, FrameGeneration) {
    json::object_t args = {
        {"param1", 100},
        {"param2", 50},
        {"color", std::vector<int>{255, 0, 0, 255}}
    };
    
    auto input = std::make_shared<input::YourInput>(args);
    cv::Mat frame = input->getFrame(0);
    
    ASSERT_FALSE(frame.empty());
    ASSERT_EQ(frame.cols, Global::WIDTH);
    ASSERT_EQ(frame.rows, Global::HEIGHT);
}
```

### Integration Test

Run the complete pipeline:

```bash
# Create test video
./video-code --file test_manual.py --generate test_output.mp4

# Verify output exists and is valid
ffmpeg -i test_output.mp4 -f null -
```

## Examples

### Complete Example: Star Shape

**Python Implementation**:

```python
# videocode/input/shape/Star.py

from videocode.input.Input import Input
from videocode.Decorators import inputCreation
from videocode.Constant import uint, rgba, YELLOW
from videocode.Checks import *
import math

class star(Input):
    """
    Creates a star shape with configurable points.
    
    Args:
        points: Number of star points (default: 5)
        outerRadius: Outer radius in pixels (default: 100)
        innerRadius: Inner radius in pixels (default: 50)
        color: RGBA color (default: YELLOW)
    """
    
    Checks = {
        "points": [isPositive, isInt],
        "outerRadius": [isPositive, isInt],
        "innerRadius": [isPositive, isInt],
        "color": [isRGBA],
    }
    
    @inputCreation
    def __init__(self,
                 points: uint = 5,
                 outerRadius: uint = 100,
                 innerRadius: uint = 50,
                 color: rgba = YELLOW) -> None:
        pass
```

**C++ Implementation**:

```cpp
// include/input/shape/Star.hpp

#pragma once

#include "input/IInput.hpp"

namespace input
{
    class Star : public IInput
    {
    private:
        int points;
        int outerRadius;
        int innerRadius;
        cv::Scalar color;
        
        std::vector<cv::Point> calculateStarPoints(int centerX, int centerY);
        
    public:
        Star(const json::object_t &args);
        cv::Mat getFrame(int time) override;
        int getDuration() const override;
        std::shared_ptr<IInput> copy() const override;
    };
}
```

```cpp
// src/input/shape/Star.cpp

#include "input/shape/Star.hpp"
#include <cmath>

namespace input
{
    Star::Star(const json::object_t &args)
    {
        points = args.at("points").get<int>();
        outerRadius = args.at("outerRadius").get<int>();
        innerRadius = args.at("innerRadius").get<int>();
        
        auto colorArray = args.at("color").get<std::vector<int>>();
        color = cv::Scalar(colorArray[0], colorArray[1], 
                          colorArray[2], colorArray[3]);
    }
    
    std::vector<cv::Point> Star::calculateStarPoints(int centerX, int centerY)
    {
        std::vector<cv::Point> starPoints;
        double angle = -M_PI / 2;  // Start from top
        double angleIncrement = M_PI / points;
        
        for (int i = 0; i < points * 2; i++) {
            int radius = (i % 2 == 0) ? outerRadius : innerRadius;
            int x = centerX + static_cast<int>(radius * cos(angle));
            int y = centerY + static_cast<int>(radius * sin(angle));
            starPoints.push_back(cv::Point(x, y));
            angle += angleIncrement;
        }
        
        return starPoints;
    }
    
    cv::Mat Star::getFrame(int time)
    {
        cv::Mat frame = cv::Mat::zeros(Global::HEIGHT, Global::WIDTH, CV_8UC4);
        
        int centerX = Global::WIDTH / 2;
        int centerY = Global::HEIGHT / 2;
        
        auto starPoints = calculateStarPoints(centerX, centerY);
        cv::fillConvexPoly(frame, starPoints, color);
        
        return frame;
    }
    
    int Star::getDuration() const
    {
        return 1;
    }
    
    std::shared_ptr<IInput> Star::copy() const
    {
        return std::make_shared<Star>(*this);
    }
}
```

**Usage**:

```python
from videocode.VideoCode import *

# Create a 7-pointed star
s = star(points=7, outerRadius=150, innerRadius=60, color=GOLD)
s.add()

# Animate it
s.apply(scale(2), duration=2).add()
s.apply(fade(), duration=1).add()
```

## Best Practices

1. **Validation**: Always validate parameters in Python using `Checks` dictionary
2. **Defaults**: Provide sensible default values for all parameters
3. **Documentation**: Write clear docstrings describing parameters and behavior
4. **Error Handling**: Handle edge cases gracefully in both Python and C++
5. **Performance**: Optimize C++ frame generation for real-time preview
6. **Memory**: Use smart pointers in C++ for automatic memory management
7. **Copying**: Implement proper copy constructor for input cloning
8. **Testing**: Write comprehensive tests for both layers

## Common Patterns

### Static vs Animated Inputs

**Static** (single frame):
```cpp
int YourInput::getDuration() const {
    return 1;
}
```

**Animated** (multiple frames):
```cpp
int YourInput::getDuration() const {
    return durationInFrames;
}

cv::Mat YourInput::getFrame(int time) {
    // Render based on time parameter
    // time ranges from 0 to getDuration()-1
}
```

### Color Handling

```cpp
// Extract RGBA from JSON
auto colorArray = args.at("color").get<std::vector<int>>();
cv::Scalar color(colorArray[0], colorArray[1], colorArray[2], colorArray[3]);
```

### Position and Alignment

Inputs inherit position from metadata. Access via:
```cpp
int x = metadata.position.x;
int y = metadata.position.y;
```

## Troubleshooting

**Input not appearing in video**:
- Verify `.add()` called in Python
- Check C++ input registered in factory
- Ensure getFrame() returns non-empty mat

**Serialization errors**:
- Verify parameter names match between Python and C++
- Check type conversions (Python tuple to C++ vector)
- Print JSON stack for debugging

**Build errors**:
- Ensure source files added to CMakeLists.txt
- Check all includes are correct
- Verify namespace consistency

**Runtime errors**:
- Add debug prints in getFrame()
- Verify Global::WIDTH and Global::HEIGHT are set
- Check for null pointer dereferences

## Additional Resources

- [Main Developer Documentation](dev.md)
- [Contributing Guide](../../CONTRIBUTING.md)
- [Adding Transformations](addEffect.md)
- [Input Base Class](../../videocode/input/Input.py)
- [IInput Interface](../../include/input/IInput.hpp)
- [Existing Input Examples](../../videocode/input/)
