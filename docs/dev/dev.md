# Developer Documentation

Welcome to the developer documentation for the Video-Code project. This comprehensive guide is intended to help developers understand the internal workings of the project and how to contribute effectively.

## Table of Contents

1. [Introduction](#introduction)
2. [Architecture Overview](#architecture-overview)
3. [Project Structure](#project-structure)
4. [Core Concepts](#core-concepts)
5. [Python-C++ Bridge](#python-c-bridge)
6. [Build System](#build-system)
7. [Development Workflow](#development-workflow)
8. [Adding New Features](#adding-new-features)
9. [Testing and Debugging](#testing-and-debugging)
10. [Code Style Guidelines](#code-style-guidelines)

## Introduction

Video-Code is a dual-language video generation framework combining Python's ease of use with C++'s performance. The project enables programmatic video creation through a DSL API while leveraging OpenCV and Qt6 for rendering and preview.

### Project Goals

- Create videos programmatically with millimetric precision
- Provide both code-based and visual editing interfaces
- Enable AI-driven video generation through a structured API
- Maintain high performance through C++ rendering engine
- Offer extensible architecture for custom inputs and transformations

## Architecture Overview

### Two-Layer Design

Video-Code follows a clear separation between the API and runtime layers:

```
┌─────────────────────────────────────┐
│     Python API Layer (DSL)          │
│   - User-facing scene definition    │
│   - Inputs (images, videos, shapes) │
│   - Transformations (effects)       │
│   - Serialization to JSON           │
└──────────────┬──────────────────────┘
               │ JSON Stack
               ▼
┌─────────────────────────────────────┐
│    C++ Runtime Layer (Compiler)     │
│   - JSON parsing and execution      │
│   - Frame rendering (OpenCV)        │
│   - Video output generation         │
│   - Qt6 live preview GUI            │
└─────────────────────────────────────┘
```

### Data Flow

1. **Scene Definition**: User writes Python script defining video scene
2. **Serialization**: Python API serializes actions to JSON stack
3. **Compilation**: C++ runtime reads JSON and executes instructions
4. **Rendering**: OpenCV generates frames based on stack execution
5. **Output**: Final video saved to file or displayed in preview

## Project Structure

```
Video-Code/
├── videocode/              # Python API Layer
│   ├── input/             # Input types (Image, Video, Text, Shapes, Groups)
│   │   ├── media/         # Image, Video, WebImage
│   │   ├── shape/         # Circle, Rectangle, Line
│   │   ├── text/          # Text, Formula
│   │   ├── group/         # Group, Incremental
│   │   └── camera/        # Camera input
│   ├── transformation/    # Transformation effects
│   │   ├── color/         # Fade, Grayscale, Blur
│   │   ├── movement/      # MoveTo, SetPosition
│   │   ├── size/          # Scale, Zoom
│   │   └── setter/        # SetAlign, SetOpacity, SetPosition
│   ├── template/          # Reusable components and utilities
│   ├── Constant.py        # Type definitions and constants
│   ├── Decorators.py      # Core decorators (@inputCreation, @autoAdd)
│   ├── Global.py          # Shared stack and metadata
│   ├── Serialize.py       # JSON serialization logic
│   └── VideoCode.py       # Main API exports
│
├── src/                   # C++ Runtime Layer
│   ├── Main.cpp           # Entry point (--generate vs preview mode)
│   ├── compiler/          # Video compilation orchestration
│   │   └── Compiler.cpp   # Main compilation logic
│   ├── core/              # Stack execution engine
│   │   └── Core.cpp       # executeStack() - core runtime
│   ├── input/             # C++ input implementations
│   │   ├── media/         # Image, Video, WebImage
│   │   ├── shape/         # Circle, Rectangle
│   │   ├── text/          # Text rendering
│   │   └── camera/        # Camera capture
│   ├── transformation/    # C++ transformation implementations
│   └── window/            # Qt6 GUI window
│       └── Window.cpp     # Live preview window
│
├── include/               # C++ Header files
│   ├── compiler/          # Compiler headers
│   ├── core/              # Core headers
│   ├── input/             # Input interface definitions
│   ├── transformation/    # Transformation interface
│   └── utils/             # Utility functions
│
├── tests/                 # Test suites
│   ├── cpp/              # C++ tests
│   └── python/           # Python tests
│
├── docs/                  # Documentation
│   ├── dev/              # Developer documentation
│   ├── user/             # User documentation
│   └── readme/           # README assets
│
├── CMakeLists.txt        # CMake build configuration
├── vcpkg.json            # C++ dependencies (opencv, qt6, json)
├── requirements.txt      # Python dependencies
└── Makefile              # Build shortcuts
```

## Core Concepts

### The Global Stack

The heart of Video-Code's architecture is the global stack stored in `Global.stack`. Every action (creating inputs, applying transformations, adding to timeline) is serialized as a JSON object in this stack.

**Example stack entry:**
```json
{
  "action": "Create",
  "type": "Circle",
  "radius": 100,
  "color": [255, 0, 0, 255]
}
```

### Input Metadata

Each input maintains metadata in `Global.metadata[index]`:
- Position (x, y coordinates)
- Alignment (left, center, right, etc.)
- Opacity (0-255)
- Other state information

### Timeline Management

The timeline is a sequence of frames. Inputs are added to the timeline using the `.add()` method, which appends frames based on:
- Input duration (for videos)
- Transformation timing (start, duration parameters)
- Current timeline position

### Automatic Add System

When `Global.automaticAdder` is enabled, transformations automatically add frames to the timeline without explicit `.add()` calls. This is controlled by the `@autoAdd` decorator.

## Python-C++ Bridge

### Serialization Process

The bridge between Python and C++ is established through JSON serialization:

1. **Python Side**: `Serialize.py` exports `serializeScene(file)` function
2. **C++ Side**: `Core.cpp` invokes Python via shell command:

```cpp
// In src/core/Core.cpp
std::string command = "python3 -c \"import sys; sys.path.append('./videocode');"
                     "from Serialize import serializeScene; "
                     "print(serializeScene('video.py'))\"";
std::string jsonStack = exec(command);
```

3. **Parsing**: C++ parses JSON using nlohmann::json
4. **Execution**: `Core::executeStack()` processes each action sequentially

### Type Mapping

Python types map to C++ as follows:

| Python Type | C++ Type |
|-------------|----------|
| `uint`, `int` | `int`, `unsigned int` |
| `ufloat`, `float` | `float`, `double` |
| `rgba` (tuple) | `cv::Scalar` |
| `str` | `std::string` |
| `bool` | `bool` |
| `list` | `std::vector` |

### Input Creation Pattern

All Python inputs use the `@inputCreation` decorator:

```python
@inputCreation
def __init__(self, radius: uint = 100, color: rgba = RED) -> None:
    # Decorator handles:
    # 1. Type checking via Checks[] validators
    # 2. Serialization to Global.stack
    # 3. Attribute assignment to self
```

The decorator automatically:
- Validates parameter types
- Adds creation action to stack
- Assigns attributes to instance
- Generates unique input ID

### Transformation Application

Transformations are applied via:

```python
def apply(self, transformation: Transformation, start=default(0), duration=default(1)):
    # Resolves default() wrappers
    # Serializes transformation to stack
    # Updates metadata via transformation.modificator()
```

## Build System

### CMake Configuration

The project uses CMake with vcpkg for dependency management:

```bash
# Configure with vcpkg toolchain
cmake -B build -DCMAKE_TOOLCHAIN_FILE=$VCPKG_ROOT/scripts/buildsystems/vcpkg.cmake

# Build
cmake --build build

# Or use Makefile shortcut
make cmake
```

### Dependencies

**C++ Dependencies** (via vcpkg.json):
- opencv4: Video/image processing
- qt6-base: GUI framework
- nlohmann-json: JSON parsing
- argparse: Command-line parsing
- cpr: HTTP requests (for WebImage)

**Python Dependencies** (via requirements.txt):
- Minimal dependencies for serialization

### Build Targets

- `video-code`: Main executable
- `video-code-lib`: Static library for testing
- Debug build: `make debug` (adds -g3 -O0 -DVC_DEBUG_ON)

### Compiler Requirements

- C++20 standard required
- GCC 13+ or Clang 15+
- Checked in CMakeLists.txt

## Development Workflow

### Setting Up Development Environment

1. **Install vcpkg**:
```bash
git clone https://github.com/Microsoft/vcpkg.git
./vcpkg/bootstrap-vcpkg.sh
export VCPKG_ROOT=/path/to/vcpkg
```

2. **Install Qt6**:
```bash
# Download from https://www.qt.io/download
export Qt6_DIR=/path/to/qt6/lib/cmake/Qt6
```

3. **Clone and build**:
```bash
git clone https://github.com/anpawo/Video-Code.git
cd Video-Code
pip install -r requirements.txt
make cmake
```

### Running the Project

**Compile Mode** (generate video):
```bash
./video-code --file video.py --generate output.mp4
```

**Preview Mode** (Qt6 GUI):
```bash
./video-code --file video.py
```

**Custom parameters**:
```bash
./video-code --file video.py --generate output.mp4 \
  --width 1920 --height 1080 --framerate 30
```

### Debugging

**Python Side**:
```python
# Enable debug prints
import videocode.Global as Global
Global.debug = True
```

**C++ Side**:
```bash
# Build with debug symbols
make debug

# Run with gdb
gdb ./video-code
(gdb) run --file video.py --generate
```

**Stack Inspection**:
```python
# In your Python script
from videocode.Global import stack
import json
print(json.dumps(stack, indent=2))
```

## Adding New Features

### Quick Links

- **[Adding Transformations](addEffect.md)** - Complete guide for new effects
- **[Adding Inputs](addInput.md)** - Guide for new input types
- **[Testing Guide](testing.md)** - Testing procedures and best practices

### General Pattern

1. **Define in Python**: Create class inheriting from `Transformation` or `Input`
2. **Register in exports**: Add to `_AllTransformation.py` or `_AllInput.py`
3. **Implement in C++**: Create corresponding C++ implementation
4. **Register in C++**: Add to transformation/input map
5. **Update CMake**: Add source files to `CMakeLists.txt`
6. **Test**: Write tests and verify functionality
7. **Document**: Add user and developer documentation

## Testing and Debugging

### Running Tests

**Python Tests**:
```bash
pytest tests/python/
```

**C++ Tests**:
```bash
make -C build
./build/tests/test_runner
```

### Common Issues

**Issue**: Python serialization fails
- **Check**: Verify `sys.path` includes `./videocode`
- **Fix**: Run from project root directory

**Issue**: C++ compilation errors with Qt6
- **Check**: `Qt6_DIR` environment variable set
- **Fix**: `export Qt6_DIR=/path/to/qt6/lib/cmake/Qt6`

**Issue**: VCPKG dependencies not found
- **Check**: `VCPKG_ROOT` environment variable set
- **Fix**: `export VCPKG_ROOT=/path/to/vcpkg`

**Issue**: Camera input shows index -1
- **Note**: Camera has special index -1 in stack (by design)

**Issue**: Input not appearing in video
- **Check**: `.add()` called or `automaticAdder` enabled
- **Fix**: Add explicit `.add()` call

### Debug Utilities

**Print stack**:
```python
from videocode.Global import stack, metadata
import json
print("Stack:", json.dumps(stack, indent=2))
print("Metadata:", metadata)
```

**C++ debug output**:
```cpp
#ifdef VC_DEBUG_ON
std::cout << "Debug: " << variableName << std::endl;
#endif
```

## Code Style Guidelines

### Python Style

- Follow PEP 8 conventions
- Use type hints for all function parameters
- Class names in camelCase starting lowercase: `circle`, `grayscale`
- Use `@inputCreation` decorator for all input constructors
- Use `@autoAdd` decorator for transformation methods

**Example**:
```python
from videocode.input.Input import Input
from videocode.Decorators import inputCreation

class myInput(Input):
    @inputCreation
    def __init__(self, param: uint = 100) -> None:
        pass  # Decorator handles everything
```

### C++ Style

- Follow modern C++ best practices (C++20)
- Use `std::shared_ptr` for input ownership
- Namespace all implementations
- Use `const` references where appropriate
- RAII for resource management

**Example**:
```cpp
#include "input/IInput.hpp"

void transformation::myEffect(std::shared_ptr<IInput> input, 
                              Register &reg, 
                              const json::object_t &args)
{
    // Implementation
}
```

### Naming Conventions

**Python**:
- Classes: `camelCase` starting lowercase (e.g., `circle`, `grayscale`)
- Functions/methods: `camelCase` starting lowercase
- Constants: `UPPER_CASE`
- Private: `_leadingUnderscore`

**C++**:
- Classes: `PascalCase` (e.g., `Circle`, `Grayscale`)
- Functions: `camelCase`
- Namespaces: `lowercase`
- Files: Match class name

### File Organization

**Python**:
```
videocode/
  category/
    _Category.py      # Base class
    Specific.py       # Specific implementation
    _AllCategory.py   # Export all
```

**C++**:
```
include/category/
  category.hpp        # Interface/declarations
src/category/
  category.cpp        # Implementation
  specific.cpp        # Specific implementations
```

## Contributing

We welcome contributions from the community! Whether you're fixing bugs, adding features, or improving documentation, your help is appreciated.

### Getting Started

For complete contribution guidelines, including:
- Code of conduct
- Development environment setup
- Coding standards
- Testing requirements
- Commit message format
- Pull request process

Please read our **[Contributing Guide](../../CONTRIBUTING.md)**.

### Quick Reference

**Pull Request Process:**

1. Fork the repository
2. Create feature branch: `git checkout -b feature/my-feature`
3. Make changes following style guidelines
4. Add tests for new functionality
5. Update documentation
6. Ensure all tests pass
7. Submit pull request with clear description

### Commit Message Format

```
type(scope): brief description

Detailed explanation of changes
- Bullet point 1
- Bullet point 2

Closes #issue_number
```

**Types**: feat, fix, docs, style, refactor, test, chore

### Review Criteria

- Code follows project style guidelines
- All tests pass
- New features include tests
- Documentation updated
- No breaking changes without discussion
- Performance impact considered

## Additional Resources

- [User Documentation](../user/user.md)
- [API Reference](../user/inputs/inputs.md)
- [Transformation Reference](../user/transformation/transformation.md)
- [FFmpeg Integration](../ffmpeg.md)
- [GitHub Repository](https://github.com/anpawo/Video-Code)
