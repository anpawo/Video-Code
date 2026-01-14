# Video-Code Plugin System

This directory contains the plugin system for Video-Code, allowing you to extend the framework with custom inputs and transformations without modifying the core codebase.

## Plugin Structure

Each plugin consists of three files:
1. **plugin.json**: Metadata and configuration
2. **plugin_py.so**: Python dynamic library
3. **plugin_cpp.so**: C++ dynamic library

## Plugin Types

### Transformation Plugins (`plugins/transformations/`)
Custom effects that can be applied to inputs (e.g., blur, custom filters, advanced animations).

### Input Plugins (`plugins/inputs/`)
Custom input sources (e.g., custom shapes, procedural patterns, special media loaders).

## Plugin JSON Schema

```json
{
  "name": "PluginName",
  "version": "1.0.0",
  "type": "transformation|input",
  "description": "Plugin description",
  "author": "Author Name",
  "python_library": "plugin_name_py.so",
  "cpp_library": "plugin_name_cpp.so",
  "class_name": "PluginClassName",
  "parameters": [
    {
      "name": "param_name",
      "type": "int|float|str|rgba|uint",
      "default": "value",
      "description": "Parameter description"
    }
  ]
}
```

## Creating a Plugin

### 1. Python Component
Create a Python class inheriting from `PluginInput` or `PluginTransformation`:

```python
from videocode.plugin.PluginBase import PluginTransformation

class MyEffect(PluginTransformation):
    def __init__(self, param1: int = 10):
        super().__init__()
        self.param1 = param1
    
    def modificator(self, meta):
        # Modify metadata if needed
        return meta
```

### 2. C++ Component
Create a C++ class inheriting from `APluginInput` or `APluginTransformation`:

```cpp
#include "plugin/PluginBase.hpp"

class MyEffect : public APluginTransformation {
public:
    MyEffect(int param1) : param1(param1) {}
    
    cv::Mat apply(cv::Mat frame) override {
        // Apply effect to frame
        return frame;
    }
private:
    int param1;
};

extern "C" APluginTransformation* create(nlohmann::json params) {
    return new MyEffect(params["param1"]);
}

extern "C" void destroy(APluginTransformation* p) {
    delete p;
}
```

### 3. Build Plugin
Add plugin to CMakeLists.txt or use provided build script.

## Loading Plugins

Plugins are automatically discovered and loaded at runtime from the `plugins/` directory.

### Python
```python
from videocode.plugin import loadPlugins
loadPlugins()

# Use plugin
myEffect = MyEffect(param1=20)
circle().apply(myEffect).add()
```

### C++
Plugins are loaded automatically by the Core when executing the stack.
