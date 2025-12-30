# Video-Code

**Create videos programmatically with Python**

Video-Code is a dual-language (Python + C++) video generation framework that enables you to create videos through code. Write Python scripts to define your video scenes, apply effects, and generate professional-quality videos with millimetric precision.

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)](https://github.com/anpawo/Video-Code)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue)](https://www.python.org/)
[![C++](https://img.shields.io/badge/c++-20-blue)](https://en.cppreference.com/w/cpp/20)

<img src="docs/readme/example.gif" alt="Video-Code Example" width="600">

## Features

- **Code-Based Video Creation**: Define videos using intuitive Python DSL
- **Rich Effects Library**: Built-in transformations for common effects
- **Real-Time Preview**: Qt6 GUI for instant visual feedback
- **High Performance**: C++ runtime with OpenCV for fast rendering
- **Extensible Architecture**: Easy to add custom inputs and transformations
- **AI-Friendly**: Structured API perfect for AI-driven video generation
- **Frame-Perfect Control**: Millimetric precision for professional results

## Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/anpawo/Video-Code.git
cd Video-Code

# Install Python dependencies
pip install -r requirements.txt

# Set up vcpkg
export VCPKG_ROOT=/path/to/vcpkg

# Set up Qt6
export Qt6_DIR=/path/to/qt6/lib/cmake/Qt6

# Build
make cmake
```

For detailed installation instructions, see [Installation Guide](docs/user/user.md#installation).

### Your First Video

Create `my_video.py`:

```python
#!/usr/bin/env python3

from videocode.VideoCode import *

# Create a red circle that moves and scales
c = circle(radius=50, color=RED)
c.setPosition(0, SH*0.5)
c.add()

# Move across screen while scaling
c.moveTo(SW, SH*0.5, duration=2).add()
c.apply(scale(2), duration=2).add()
```

Generate the video:

```bash
./video-code --file my_video.py --generate output.mp4
```

Or preview it:

```bash
./video-code --file my_video.py
```

## Examples

### Text Animation

```python
from videocode.VideoCode import *

# Animated title
title = text("Video-Code", fontSize=72, color=WHITE)
title.setPosition(SW*0.5, SH*0.3)

# Fade in, show, fade out
title.apply(fade(type="in"), duration=1).add()
title.add(duration=2)
title.apply(fade(type="out"), duration=1).add()
```

### Image Slideshow

```python
from videocode.VideoCode import *

for img_path in ["img1.jpg", "img2.jpg", "img3.jpg"]:
    img = image(img_path)
    img.apply(fade(type="in"), duration=0.5).add()
    img.add(duration=2)
    img.apply(fade(type="out"), duration=0.5).add()
```

### Multiple Elements

```python
from videocode.VideoCode import *

# Background
rectangle(width=SW, height=SH, color=(30, 30, 30, 255)).add(duration=5)

# Title
title = text("My Video", fontSize=64, color=WHITE)
title.setPosition(SW*0.5, SH*0.2).add(duration=5)

# Animated circle
c = circle(radius=30, color=RED)
c.setPosition(SW*0.5, SH*0.5)
c.add()
c.apply(scale(2), duration=2).add()
c.apply(scale(0.5), duration=2).add()
```

More examples in the [test/](test/) directory.

## Architecture

Video-Code uses a two-layer architecture:

```
┌─────────────────────────────────┐
│   Python API Layer (DSL)        │
│   - User-facing scene definition│
│   - Inputs and Transformations  │
│   - Serialization to JSON       │
└──────────────┬──────────────────┘
               │ JSON Stack
               ▼
┌─────────────────────────────────┐
│   C++ Runtime Layer (Compiler)  │
│   - JSON parsing & execution    │
│   - Frame rendering (OpenCV)    │
│   - Video output generation     │
│   - Qt6 live preview GUI        │
└─────────────────────────────────┘
```

**Python** provides the user-friendly API, while **C++** handles the heavy lifting of video rendering for optimal performance.

## Available Inputs

### Media
- `image()` - Load images (JPG, PNG, etc.)
- `video()` - Load video files
- `webImage()` - Load images from URLs

### Shapes
- `circle()` - Create circles
- `rectangle()` - Create rectangles
- `square()` - Create squares
- `line()` - Draw lines

### Text
- `text()` - Create text labels
- `formula()` - Render LaTeX formulas

### Groups
- `group()` - Group multiple inputs
- `incremental()` - Create incremental groups

### Camera
- `camera()` - Capture from webcam

## Available Transformations

### Color Effects
- `fade()` - Fade in/out effects
- `grayscale()` - Convert to grayscale
- `blur()` - Apply Gaussian blur

### Movement
- `moveTo()` - Move to position over time
- `setPosition()` - Set immediate position

### Size Effects
- `scale()` - Scale input size
- `zoom()` - Zoom into input

### Setters
- `setOpacity()` - Set transparency
- `setAlign()` - Set alignment

## Documentation

### For Users
- [User Guide](docs/user/user.md) - Complete usage guide
- [API Reference](docs/user/api_reference.md) - Full API documentation
- [Input Documentation](docs/user/inputs/inputs.md) - All input types
- [Transformation Documentation](docs/user/transformation/transformation.md) - All transformations

### For Developers
- [Developer Guide](docs/dev/dev.md) - Architecture and internals
- [Adding Inputs](docs/dev/addInput.md) - How to add new input types
- [Adding Transformations](docs/dev/addEffect.md) - How to add new effects
- [Testing Guide](docs/dev/testing.md) - Testing and debugging

## Command-Line Options

```bash
# Generate video
./video-code --file script.py --generate output.mp4

# Custom dimensions
./video-code --file script.py --generate output.mp4 --width 1920 --height 1080

# Custom framerate
./video-code --file script.py --generate output.mp4 --framerate 60

# Preview mode (Qt6 GUI)
./video-code --file script.py

# Help
./video-code --help
```

## Project Structure

```
Video-Code/
├── videocode/           # Python API Layer
│   ├── input/          # Input types
│   ├── transformation/ # Transformations
│   ├── template/       # Reusable templates
│   └── *.py           # Core API files
├── src/                # C++ Runtime Layer
│   ├── input/          # C++ input implementations
│   ├── transformation/ # C++ transformation implementations
│   ├── compiler/       # Video compilation
│   ├── core/           # Stack execution
│   └── window/         # Qt6 GUI
├── include/            # C++ headers
├── docs/               # Documentation
│   ├── dev/           # Developer docs
│   └── user/          # User docs
├── tests/              # Test suites
└── test/               # Example scripts
```

## Requirements

### Runtime
- Python 3.8+
- CMake 3.20+
- GCC 13+ or Clang 15+ (C++20 support)
- Qt6 (for GUI preview)

### Dependencies (via vcpkg)
- OpenCV 4
- nlohmann-json
- argparse
- cpr (HTTP requests)

## Building from Source

```bash
# Configure with vcpkg
cmake -B build -DCMAKE_TOOLCHAIN_FILE=$VCPKG_ROOT/scripts/buildsystems/vcpkg.cmake

# Build
cmake --build build

# Copy binary
cp build/video-code .

# Or use Makefile shortcuts
make cmake    # Build release
make debug    # Build with debug symbols
```

## Contributing

Contributions are welcome! We value all contributions, from bug reports to new features.

**Quick Start:**

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Update documentation
7. Submit a pull request

**Detailed Guidelines:**

Please read our [Contributing Guide](CONTRIBUTING.md) for:
- Code of conduct
- Development environment setup
- Coding standards and best practices
- Testing requirements
- Pull request process
- Adding new features

Also see:
- [Developer Guide](docs/dev/dev.md) - Project architecture and internals
- [Adding Inputs](docs/dev/addInput.md) - How to add new input types
- [Adding Transformations](docs/dev/addEffect.md) - How to add new effects

## Use Cases

- **Social Media Content**: Automate video generation for platforms
- **Data Visualization**: Create dynamic charts and infographics
- **Educational Videos**: Programmatically generate teaching materials
- **Video Templates**: Build reusable video templates
- **AI Video Generation**: Enable AI to create videos through code
- **Batch Processing**: Generate multiple videos from data

## Patch Notes

<details>
<summary><strong>Recent Updates</strong></summary>

### Version 0.4.0 (2025-04-08)
- Feature: `start` and `duration` parameters for transformations
- Rework: Inputs kept on video by default
- Feature: `wait()` function to freeze screen
- Transformation: `setPosition()` added
- Rework: `move()` renamed to `moveTo()`
- Input: `group()` added

### Version 0.3.0 (2025-03-24)
- Input: `rectangle()` and `circle()` shapes
- Transformation: `scale()` and `zoom()`
- Rework: Effects duration system
- Transformation: `grayscale()`

### Version 0.2.0 (2025-03-06)
- Feature: Keep last frame on screen
- Rework: Single global stack
- Transformation: `repeat()`
- Input: `text()`

### Version 0.1.0 (2025-02-20)
- Initial release
- Basic inputs: image, video
- Basic transformations: move, fade
- Qt6 preview window
- Video generation

</details>

## Roadmap

- [ ] More shape primitives (triangles, polygons, arcs)
- [ ] Audio support and synchronization
- [ ] Advanced text formatting and animations
- [ ] 3D transformations
- [ ] Particle systems
- [ ] Video filters and color grading
- [ ] Plugin system for extensions
- [ ] Web-based editor interface
- [ ] Template marketplace
- [ ] Performance optimizations

## Performance

Video-Code is designed for performance:

- C++ runtime for fast frame rendering
- OpenCV for optimized image operations
- Efficient memory management with smart pointers
- Parallel processing support (planned)

Typical performance: 1080p video at 30 FPS generates at 2-5x real-time speed on modern hardware.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/anpawo/Video-Code/issues)
- **Discussions**: [GitHub Discussions](https://github.com/anpawo/Video-Code/discussions)

## Acknowledgments

- Built with [OpenCV](https://opencv.org/) for image processing
- Uses [Qt6](https://www.qt.io/) for GUI
- Powered by [vcpkg](https://vcpkg.io/) for dependency management
- JSON parsing with [nlohmann/json](https://github.com/nlohmann/json)

## Project Vision

The goal of Video-Code is to make video creation as accessible as writing code. By providing a programmatic interface to video generation, we enable:

1. **Precision**: Create videos with frame-perfect accuracy
2. **Automation**: Generate videos at scale from data
3. **AI Integration**: Enable AI systems to create videos through structured code
4. **Reproducibility**: Version-controlled, repeatable video generation
5. **Accessibility**: Lower the barrier to entry for video creation

Whether you're creating content for social media, generating data visualizations, or building AI-powered video tools, Video-Code provides the foundation for programmatic video creation.

---

**Made with code, not timelines**

[GitHub Repository](https://github.com/anpawo/Video-Code) | [Documentation](docs/) | [Examples](test/)
