# Contributing to Video-Code

Thank you for your interest in contributing to Video-Code! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Development Environment Setup](#development-environment-setup)
4. [Project Structure](#project-structure)
5. [Development Workflow](#development-workflow)
6. [Coding Standards](#coding-standards)
7. [Testing Requirements](#testing-requirements)
8. [Submitting Changes](#submitting-changes)
9. [Adding New Features](#adding-new-features)
10. [Documentation](#documentation)
11. [Review Process](#review-process)
12. [Community](#community)

## Introduction

Welcome to the Video-Code contribution guide! Whether you're fixing bugs, adding new features, improving documentation, or helping with testing, your contributions are valuable to us.

## Getting Started

### Prerequisites

Before contributing, ensure you have:

- Git installed and configured
- Python 3.8 or higher
- CMake 3.20 or higher
- GCC 13+ or Clang 15+ (C++20 support)
- vcpkg package manager
- Qt6 (for GUI development)
- Basic knowledge of Python and C++

### Finding Ways to Contribute

- Browse [open issues](https://github.com/anpawo/Video-Code/issues)
- Check the [roadmap](README.md#roadmap) for planned features
- Improve documentation
- Fix bugs or improve performance
- Add new inputs or transformations

## Development Environment Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then:
git clone https://github.com/YOUR_USERNAME/Video-Code.git
cd Video-Code

# Add upstream remote
git remote add upstream https://github.com/anpawo/Video-Code.git
```

### 2. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-cov black flake8
```

### 3. Set Up vcpkg

```bash
# If you don't have vcpkg:
git clone https://github.com/Microsoft/vcpkg.git
cd vcpkg
./bootstrap-vcpkg.sh
export VCPKG_ROOT=$(pwd)
cd ..

# Add to your shell profile (.bashrc, .zshrc, etc.):
export VCPKG_ROOT=/path/to/vcpkg
```

### 4. Install Qt6

Download and install Qt6 from [https://www.qt.io/download](https://www.qt.io/download)

```bash
# Set Qt6_DIR environment variable
export Qt6_DIR=/path/to/qt6/lib/cmake/Qt6
```

### 5. Build the Project

```bash
# Configure and build
cmake -B build -DCMAKE_TOOLCHAIN_FILE=$VCPKG_ROOT/scripts/buildsystems/vcpkg.cmake
cmake --build build

# Or use Makefile
make cmake

# For development with debug symbols
make debug
```

### 6. Verify Installation

```bash
# Test the build
./video-code --help

# Run tests
pytest tests/python/
./build/tests/test_runner
```

## Project Structure

Understanding the project structure is crucial for effective contribution:

```
Video-Code/
├── videocode/              # Python API Layer
│   ├── input/             # Input types (Image, Video, Shapes, etc.)
│   ├── transformation/    # Transformation effects
│   ├── template/          # Reusable components
│   ├── Constant.py        # Type definitions and constants
│   ├── Decorators.py      # Core decorators
│   ├── Global.py          # Global stack and metadata
│   ├── Serialize.py       # JSON serialization
│   └── VideoCode.py       # Main API exports
│
├── src/                   # C++ Runtime Layer
│   ├── Main.cpp           # Entry point
│   ├── compiler/          # Video compilation
│   ├── core/              # Stack execution engine
│   ├── input/             # C++ input implementations
│   ├── transformation/    # C++ transformation implementations
│   └── window/            # Qt6 GUI
│
├── include/               # C++ Headers
├── tests/                 # Test suites
├── docs/                  # Documentation
│   ├── dev/              # Developer documentation
│   └── user/             # User documentation
└── test/                  # Example scripts
```

## Development Workflow

### 1. Create a Branch

```bash
# Update your main branch
git checkout main
git pull upstream main

# Create a feature branch
git checkout -b feature/my-feature
# or for bug fixes:
git checkout -b fix/issue-description
```

### Branch Naming Conventions

- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation changes
- `refactor/` - Code refactoring
- `test/` - Test additions/improvements
- `perf/` - Performance improvements

### 2. Make Changes

- Write clear, focused commits
- Follow coding standards
- Add tests for new functionality
- Update documentation
- Keep commits atomic and logical

### 3. Test Your Changes

```bash
# Run Python tests
pytest tests/python/ -v

# Run C++ tests
./build/tests/test_runner

# Test manually
./video-code --file test/my_test.py --generate output.mp4

# Check code style
black videocode/
flake8 videocode/
```

### 4. Commit Changes

```bash
# Stage your changes
git add .

# Commit with a descriptive message
git commit -m "feat: add triangle shape input

- Implement Python triangle class
- Add C++ triangle rendering
- Include tests and documentation
- Update API reference

Closes #123"
```

### Commit Message Format

Use conventional commits format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Test additions/improvements
- `perf`: Performance improvements
- `chore`: Build process, dependencies, etc.

**Example:**
```
feat(input): add triangle shape support

Implement triangle input with configurable base and height.
Includes Python API and C++ rendering using OpenCV.

- Add Triangle.py with parameter validation
- Implement C++ triangle rendering
- Add unit tests for both layers
- Update API documentation

Closes #45
```

## Coding Standards

### Python Style

Follow PEP 8 with these specifics:

**Naming Conventions:**
- Classes: `camelCase` starting lowercase (e.g., `circle`, `grayscale`)
- Functions/methods: `camelCase` starting lowercase
- Constants: `UPPER_CASE`
- Private members: `_leadingUnderscore`

**Type Hints:**
Always use type hints for function parameters and return types:

```python
def myFunction(radius: uint, color: rgba = RED) -> None:
    pass
```

**Documentation:**
Use docstrings for all classes and public methods:

```python
class myInput(Input):
    """
    Brief description.
    
    Args:
        param1: Description of param1
        param2: Description of param2
    """
```

**Code Formatting:**
- Use 4 spaces for indentation
- Maximum line length: 100 characters
- Use `black` for automatic formatting:
  ```bash
  black videocode/
  ```

**Example:**

```python
from videocode.input.Input import Input
from videocode.Decorators import inputCreation
from videocode.Constant import uint, rgba, RED
from videocode.Checks import *

class myInput(Input):
    """
    Description of input.
    
    Args:
        size: Size parameter
        color: RGBA color tuple
    """
    
    Checks = {
        "size": [isPositive, isInt],
        "color": [isRGBA],
    }
    
    @inputCreation
    def __init__(self, size: uint = 100, color: rgba = RED) -> None:
        pass
```

### C++ Style

Follow modern C++ best practices (C++20):

**Naming Conventions:**
- Classes: `PascalCase` (e.g., `Circle`, `Grayscale`)
- Functions: `camelCase`
- Namespaces: `lowercase`
- Constants: `UPPER_CASE`
- Private members: `camelCase`

**Code Organization:**
- Use header guards or `#pragma once`
- Include guards in all headers
- Separate declaration (.hpp) from implementation (.cpp)
- Use namespaces to organize code

**Modern C++ Features:**
- Use `std::shared_ptr` and `std::unique_ptr`
- Use `auto` where type is obvious
- Use range-based for loops
- Use `nullptr` instead of `NULL`
- Use `const` references where appropriate

**Example:**

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
        
        // Implement triangle rendering
        // ...
        
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

### Code Quality

- Write self-documenting code with clear variable names
- Keep functions small and focused
- Handle errors appropriately
- Avoid code duplication
- Comment complex logic
- Use meaningful names

## Testing Requirements

All contributions must include appropriate tests.

### Python Tests

Location: `tests/python/`

**Test Structure:**

```python
import sys
sys.path.append('./videocode')

from videocode.VideoCode import *
import pytest

class TestMyFeature:
    """Test suite for MyFeature."""
    
    def setup_method(self):
        """Reset state before each test."""
        from videocode.Global import stack, metadata
        stack.clear()
        metadata.clear()
    
    def test_creation(self):
        """Test creating the feature."""
        feature = myFeature(param=100)
        assert feature.param == 100
    
    def test_serialization(self):
        """Test serialization to stack."""
        feature = myFeature(param=100)
        inp = circle()
        inp.apply(feature)
        inp.add()
        
        from videocode.Global import stack
        assert len(stack) > 0
```

**Run Tests:**

```bash
# Run all tests
pytest tests/python/ -v

# Run specific test file
pytest tests/python/test_myfeature.py -v

# Run with coverage
pytest tests/python/ --cov=videocode --cov-report=html
```

### C++ Tests

Location: `tests/cpp/`

**Test Structure:**

```cpp
#include <gtest/gtest.h>
#include "myfeature.hpp"

TEST(MyFeatureTest, BasicFunctionality) {
    // Arrange
    MyFeature feature;
    
    // Act
    auto result = feature.process();
    
    // Assert
    EXPECT_TRUE(result);
    ASSERT_NE(result, nullptr);
}
```

**Run Tests:**

```bash
# Build and run tests
cmake --build build
./build/tests/test_runner

# Run specific test
./build/tests/test_runner --gtest_filter=MyFeatureTest.*
```

### Test Requirements

- All new features must include tests
- Aim for 100% code coverage
- Test edge cases and error conditions

## Submitting Changes

### Before Submitting

Checklist:

- [ ] Code follows project style guidelines
- [ ] All tests pass locally
- [ ] New tests added for new functionality
- [ ] Documentation updated
- [ ] Commit messages follow convention
- [ ] Branch is up to date with main
- [ ] No merge conflicts

### Creating a Pull Request

1. Push your branch to your fork
2. Go to the [Video-Code repository](https://github.com/anpawo/Video-Code)
3. Click "New Pull Request"
4. Select your fork and branch
5. Fill out the PR template:

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Related Issues
Closes #123
```

### Pull Request Guidelines

- Keep PRs focused on a single feature/fix
- Provide clear description of changes
- Reference related issues
- Include screenshots/videos for UI changes
- Respond to review feedback promptly
- Keep PR size manageable (< 500 lines when possible)

### Proposing Major Changes

For significant changes:

1. Open an issue to discuss the proposal
2. Explain the problem and proposed solution
3. Get feedback from maintainers
4. Create a design document if needed
5. Implement after approval

## Documentation

Documentation is as important as code.

### What to Document

- New features and how to use them
- API changes and migration guides
- Configuration options
- Examples and tutorials
- Architecture decisions

### Where to Document

- **Code comments**: Complex logic and algorithms
- **Docstrings**: All public APIs
- **User docs**: `docs/user/` - How to use features
- **Dev docs**: `docs/dev/` - How to contribute/extend
- **README**: High-level project information
- **API reference**: `docs/user/api_reference.md`

### Documentation Style

- Write clearly and concisely
- Use code examples
- Include both simple and advanced examples
- Keep formatting consistent
- Update existing docs when changing functionality

## Review Process

### What to Expect

1. **Automated Checks**: CI/CD runs tests and linters
2. **Review**: Code review by project maintainers
3. **Feedback**: Suggestions for improvements
4. **Iteration**: Make requested changes
5. **Approval**: PR approved when ready
6. **Merge**: Merged into main branch

### Addressing Feedback

- Respond to all comments
- Push additional commits (don't force push)

## Community

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and ideas
- **Pull Requests**: Code contributions and reviews

### Getting Help

- Review [documentation](docs/)
- Search [existing issues](https://github.com/anpawo/Video-Code/issues)
- Ask in [discussions](https://github.com/anpawo/Video-Code/discussions)
- Tag maintainers for urgent issues

### Recognition

Contributors are recognized in:

- Git history
- Release notes
- Contributors list
- Special acknowledgments for significant contributions

## Additional Resources

### Documentation

- [Main README](README.md)
- [Developer Guide](docs/dev/dev.md)
- [User Guide](docs/user/user.md)
- [API Reference](docs/user/api_reference.md)
- [Testing Guide](docs/dev/testing.md)
