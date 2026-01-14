# Building and Using Plugins

This guide explains how to build and use the Video-Code plugin system.

## Prerequisites

- CMake 3.20+
- C++20 compatible compiler (GCC 13+)
- Python 3.10+
- OpenCV 4.x
- vcpkg for dependency management

## Building Plugins

### 1. Build C++ Plugins

The C++ plugins are built automatically when you build the main project:

```bash
cd build
cmake ..
make
```

This will compile all C++ plugins and place them in their respective plugin directories:
- `plugins/transformations/<name>/<name>_cpp.so`
- `plugins/inputs/<name>/<name>_cpp.so`

### 2. Python Plugins

Python plugins can be used directly as `.py` files or compiled to `.so` for distribution.

#### Option A: Use as Python Source (Development)
No compilation needed - just import directly.

#### Option B: Compile with Cython (Production)
```bash
cd plugins/transformations/blur
cython --embed -3 blur_plugin.py -o blur_plugin.c
gcc -shared -pthread -fPIC -fwrapv -O2 -Wall -fno-strict-aliasing \
    -I/usr/include/python3.10 \
    -o blur_py.so blur_plugin.c \
    -lpython3.10
```

## Using Plugins in Python

```python
from videocode import *
from videocode.plugin import loadAllPlugins

# Load all plugins
loadAllPlugins()

# Use transformation plugin
from videocode.plugin import Blur
circle().apply(Blur(kernel_size=15, sigma=3.0)).add()

# Use input plugin  
from videocode.plugin import Gradient
grad = Gradient(color1=RED, color2=BLUE, direction="vertical")
grad.add(duration=3)

end()
```

## Creating a New Plugin

### Transformation Plugin Example

#### 1. Create Plugin Directory
```bash
mkdir -p plugins/transformations/sepia
cd plugins/transformations/sepia
```

#### 2. Create plugin.json
```json
{
  "name": "Sepia",
  "version": "1.0.0",
  "type": "transformation",
  "description": "Applies sepia tone effect",
  "author": "Your Name",
  "python_library": "sepia_py.so",
  "cpp_library": "sepia_cpp.so",
  "class_name": "Sepia",
  "parameters": [
    {
      "name": "intensity",
      "type": "float",
      "default": 1.0,
      "description": "Effect intensity (0.0 to 1.0)"
    }
  ]
}
```

#### 3. Create Python Plugin (sepia_plugin.py)
```python
from videocode.plugin.PluginBase import PluginTransformation
from videocode.Global import Metadata
from typing import Any

class Sepia(PluginTransformation):
    def __init__(self, intensity: float = 1.0):
        super().__init__()
        self.intensity = max(0.0, min(1.0, intensity))
    
    def modificator(self, meta: Metadata) -> Metadata:
        return meta
    
    def _getParams(self) -> dict[str, Any]:
        return {"intensity": self.intensity}
```

#### 4. Create C++ Plugin (sepia_cpp.cpp)
```cpp
#include "plugin/PluginBase.hpp"
#include <opencv2/opencv.hpp>

class SepiaPlugin : public vc::APluginTransformation {
public:
    SepiaPlugin(double intensity) : intensity_(intensity) {}
    
    cv::Mat apply(cv::Mat frame) override {
        cv::Mat result;
        cv::Mat kernel = (cv::Mat_<float>(3,3) <<
            0.272, 0.534, 0.131,
            0.349, 0.686, 0.168,
            0.393, 0.769, 0.189);
        
        cv::transform(frame, result, kernel);
        
        // Blend with original based on intensity
        cv::addWeighted(frame, 1.0 - intensity_, 
                       result, intensity_, 0, result);
        
        return result;
    }
    
    std::string getName() const override { return "Sepia"; }
    
    nlohmann::json serialize() const override {
        return {{"plugin_name", "Sepia"}, {"intensity", intensity_}};
    }

private:
    double intensity_;
};

extern "C" {
    vc::APluginTransformation* create(const nlohmann::json& params) {
        return new SepiaPlugin(params.value("intensity", 1.0));
    }
    
    void destroy(vc::APluginTransformation* plugin) {
        delete plugin;
    }
}
```

#### 5. Register in CMake
Add to `plugins/CMakeLists.txt`:
```cmake
add_plugin_cpp(sepia transformation 
    ${CMAKE_SOURCE_DIR}/plugins/transformations/sepia/sepia_cpp.cpp)
```

#### 6. Build and Use
```bash
cd build
make
```

```python
from videocode.plugin import Sepia
circle().apply(Sepia(intensity=0.8)).add()
```

## Input Plugin Example

Follow the same structure but:
- Place in `plugins/inputs/<name>/`
- Set `"type": "input"` in plugin.json
- Inherit from `PluginInput` (Python) and `APluginInput` (C++)
- Implement `generate()` instead of `apply()`

## Plugin API Reference

### Python Base Classes

#### PluginTransformation
```python
class PluginTransformation(ABC):
    def modificator(self, meta: Metadata) -> Metadata: ...
    def serialize(self) -> dict[str, Any]: ...
    def _getParams(self) -> dict[str, Any]: ...  # Implement this
```

#### PluginInput
```python
class PluginInput(ABC):
    def apply(self, transformation): ...
    def add(self, duration: uint = 1): ...
    def serialize(self) -> dict[str, Any]: ...
    def _getParams(self) -> dict[str, Any]: ...  # Implement this
```

### C++ Base Classes

#### APluginTransformation
```cpp
class APluginTransformation {
    virtual cv::Mat apply(cv::Mat frame) = 0;
    virtual std::string getName() const = 0;
    virtual nlohmann::json serialize() const = 0;
};
```

#### APluginInput
```cpp
class APluginInput {
    virtual cv::Mat generate(int width, int height, int frameNumber) = 0;
    virtual std::string getName() const = 0;
    virtual nlohmann::json serialize() const = 0;
};
```

### Required Factory Functions (C++)
```cpp
extern "C" {
    PluginType* create(const nlohmann::json& params);
    void destroy(PluginType* plugin);
}
```

## Troubleshooting

### Plugin Not Found
- Verify plugin.json exists and is valid JSON
- Check that .so files are in the plugin directory
- Ensure CMake built the plugin successfully

### Symbol Not Found
- Verify `extern "C"` is used for create/destroy functions
- Check function signatures match expected types
- Use `nm -D <plugin>.so` to inspect symbols

### Import Errors
- Ensure `loadAllPlugins()` is called before using plugins
- Check Python path includes videocode directory
- Verify plugin class name matches plugin.json

### Build Errors
- Update CMake to 3.20+
- Install missing dependencies via vcpkg
- Check compiler supports C++20

## Plugin Distribution

To distribute plugins:
1. Package the plugin directory with all three files
2. Include build instructions or pre-compiled .so files
3. Document dependencies and parameters
4. Provide usage examples

Users install by:
1. Copying plugin directory to `plugins/transformations/` or `plugins/inputs/`
2. Running `make` to build C++ component
3. Calling `loadAllPlugins()` in their scripts
