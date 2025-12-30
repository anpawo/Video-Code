# Video-Code API Reference

Complete API reference for Video-Code inputs and transformations.

## Table of Contents

- [Inputs](#inputs)
  - [Media](#media-inputs)
  - [Shapes](#shape-inputs)
  - [Text](#text-inputs)
  - [Groups](#group-inputs)
  - [Camera](#camera-input)
- [Transformations](#transformations)
  - [Color](#color-transformations)
  - [Movement](#movement-transformations)
  - [Size](#size-transformations)
  - [Setters](#setter-transformations)
- [Global Constants](#global-constants)

## Inputs

### Media Inputs

#### image

Load an image file.

**Parameters:**
- `path` (str): Path to image file
- `width` (uint, optional): Width in pixels
- `height` (uint, optional): Height in pixels

**Example:**
```python
img = image("photo.jpg")
img.add()
```

#### video

Load a video file.

**Parameters:**
- `path` (str): Path to video file
- `width` (uint, optional): Width in pixels
- `height` (uint, optional): Height in pixels

**Example:**
```python
v = video("clip.mp4")
v.add()
```

#### webImage

Load an image from a URL.

**Parameters:**
- `url` (str): URL to image
- `width` (uint, optional): Width in pixels
- `height` (uint, optional): Height in pixels

**Example:**
```python
web_img = webImage("https://example.com/image.jpg")
web_img.add()
```

### Shape Inputs

#### circle

Create a circle shape.

**Parameters:**
- `radius` (uint): Circle radius in pixels (default: 100)
- `color` (rgba): RGBA color tuple (default: RED)

**Example:**
```python
c = circle(radius=150, color=BLUE)
c.add()
```

#### rectangle

Create a rectangle shape.

**Parameters:**
- `width` (uint): Width in pixels (default: 200)
- `height` (uint): Height in pixels (default: 100)
- `color` (rgba): RGBA color tuple (default: RED)
- `cornerRadius` (uint, optional): Corner radius for rounded rectangles

**Example:**
```python
r = rectangle(width=300, height=150, color=GREEN)
r.add()
```

#### square

Create a square shape (convenience function).

**Parameters:**
- `side` (uint): Side length in pixels (default: 100)
- `color` (rgba): RGBA color tuple (default: RED)

**Example:**
```python
s = square(side=100, color=YELLOW)
s.add()
```

#### line

Create a line.

**Parameters:**
- `x1` (int): Starting x coordinate
- `y1` (int): Starting y coordinate
- `x2` (int): Ending x coordinate
- `y2` (int): Ending y coordinate
- `color` (rgba): RGBA color tuple (default: WHITE)
- `thickness` (uint): Line thickness in pixels (default: 2)

**Example:**
```python
l = line(x1=0, y1=0, x2=200, y2=200, color=WHITE, thickness=5)
l.add()
```

### Text Inputs

#### text

Create text.

**Parameters:**
- `content` (str): Text content
- `fontSize` (uint): Font size in points (default: 32)
- `color` (rgba): RGBA color tuple (default: WHITE)
- `fontFamily` (str, optional): Font family name
- `bold` (bool): Bold text (default: False)
- `italic` (bool): Italic text (default: False)

**Example:**
```python
t = text("Hello World", fontSize=48, color=WHITE, bold=True)
t.add()
```

#### formula

Create a mathematical formula using LaTeX.

**Parameters:**
- `latex` (str): LaTeX formula string
- `fontSize` (uint): Font size (default: 32)
- `color` (rgba): RGBA color tuple (default: WHITE)

**Example:**
```python
f = formula(r"\int_0^\infty e^{-x^2} dx", fontSize=40)
f.add()
```

### Group Inputs

#### group

Group multiple inputs together.

**Parameters:**
- `*inputs`: Variable number of Input objects

**Example:**
```python
g = group(
    circle(radius=50, color=RED),
    square(side=100, color=BLUE)
)
g.setPosition(SW*0.5, SH*0.5)
g.add()
```

#### incremental

Create a group with incremental transformations.

**Parameters:**
- `inputs` (list): List of Input objects
- `xOffset` (int, optional): Horizontal spacing
- `yOffset` (int, optional): Vertical spacing

**Example:**
```python
inc = incremental(
    [circle(radius=30) for _ in range(5)],
    xOffset=80
)
inc.add()
```

### Camera Input

#### camera

Capture from camera.

**Parameters:**
- `deviceId` (int): Camera device ID (default: 0)
- `width` (uint, optional): Capture width
- `height` (uint, optional): Capture height

**Example:**
```python
cam = camera()
cam.add(duration=5)  # Record 5 seconds
```

## Transformations

### Color Transformations

#### fade

Fade in, out, or both.

**Parameters:**
- `type` (str): Fade type - "in", "out", or "both" (default: "both")
- `intensity` (ufloat): Fade intensity 0.0-1.0 (default: 1.0)

**Usage:**
```python
input.apply(fade(type="in"), duration=1).add()
```

#### grayscale

Convert to grayscale.

**Parameters:**
- `intensity` (ufloat): Effect intensity 0.0-1.0 (default: 1.0)

**Usage:**
```python
input.apply(grayscale()).add()
```

#### blur

Apply Gaussian blur.

**Parameters:**
- `amount` (uint): Blur amount in pixels (default: 5)

**Usage:**
```python
input.apply(blur(amount=10)).add()
```

### Movement Transformations

#### moveTo

Move input to a specific position over time.

**Parameters:**
- `x` (int): Target x coordinate
- `y` (int): Target y coordinate
- `duration` (sec): Movement duration in seconds
- `easing` (function, optional): Easing function

**Usage:**
```python
input.moveTo(SW*0.5, SH*0.5, duration=2).add()
```

#### setPosition

Immediately set position.

**Parameters:**
- `x` (int): X coordinate
- `y` (int): Y coordinate

**Usage:**
```python
input.setPosition(100, 200).add()
```

### Size Transformations

#### scale

Scale the input.

**Parameters:**
- `factor` (ufloat): Scale factor (default: 1.0)

**Usage:**
```python
input.apply(scale(2), duration=1).add()  # Scale to 2x over 1 second
```

#### zoom

Zoom into the input.

**Parameters:**
- `factor` (ufloat): Zoom factor (default: 2.0)

**Usage:**
```python
input.apply(zoom(3), duration=2).add()
```

### Setter Transformations

#### setOpacity

Set opacity/transparency.

**Parameters:**
- `opacity` (ufloat): Opacity 0.0-1.0 (default: 1.0)

**Usage:**
```python
input.setOpacity(0.5).add()  # 50% transparent
```

#### setAlign

Set alignment.

**Parameters:**
- `alignment` (str): Alignment - "left", "center", "right", "top", "bottom", etc.

**Usage:**
```python
input.setAlign("center").add()
```

## Input Methods

All inputs support these methods:

### add(duration=default(1))

Add input to timeline.

**Parameters:**
- `duration` (sec, optional): Duration in seconds

```python
input.add()
input.add(duration=2)
```

### apply(transformation, start=default(0), duration=default(1))

Apply a transformation to the input.

**Parameters:**
- `transformation` (Transformation): Transformation to apply
- `start` (sec): Start time relative to input
- `duration` (sec): Transformation duration

```python
input.apply(fade()).add()
input.apply(scale(2), duration=2).add()
```

### keep()

Keep the last frame on screen.

```python
input.keep()
```

### setPosition(x, y)

Set input position.

**Parameters:**
- `x` (int): X coordinate
- `y` (int): Y coordinate

```python
input.setPosition(100, 200)
```

### moveTo(x, y, duration=1)

Move to position over time.

**Parameters:**
- `x` (int): Target x coordinate
- `y` (int): Target y coordinate
- `duration` (sec): Movement duration

```python
input.moveTo(SW*0.5, SH*0.5, duration=2).add()
```

### setOpacity(opacity)

Set opacity.

**Parameters:**
- `opacity` (ufloat): 0.0-1.0

```python
input.setOpacity(0.5)
```

### setAlign(alignment)

Set alignment.

**Parameters:**
- `alignment` (str): Alignment string

```python
input.setAlign("center")
```

## Global Constants

### Screen Dimensions

```python
SW  # Screen width (default: 1920)
SH  # Screen height (default: 1080)
```

### Colors (RGBA tuples)

```python
RED = (255, 0, 0, 255)
GREEN = (0, 255, 0, 255)
BLUE = (0, 0, 255, 255)
WHITE = (255, 255, 255, 255)
BLACK = (0, 0, 0, 255)
YELLOW = (255, 255, 0, 255)
CYAN = (0, 255, 255, 255)
MAGENTA = (255, 0, 255, 255)
```

### Time Functions

```python
wait(seconds)  # Wait for specified seconds
sec(frames)    # Convert frames to seconds
t(seconds)     # Time in seconds
```

## Type System

### Custom Types

- `uint`: Unsigned integer
- `ufloat`: Unsigned float
- `rgba`: RGBA color tuple (R, G, B, A) with values 0-255
- `sec`: Time in seconds
- `default(value)`: Optional parameter with fallback

### Example Usage

```python
def myFunction(radius: uint = 100, color: rgba = RED, duration: sec = 1.0):
    pass
```

## Examples

### Complete Example 1: Animated Circle

```python
from videocode.VideoCode import *

# Create and position circle
c = circle(radius=50, color=RED)
c.setPosition(0, SH*0.5)
c.add()

# Move across screen
c.moveTo(SW, SH*0.5, duration=2).add()

# Scale while moving
c.apply(scale(2), duration=2).add()

# Fade out
c.apply(fade(type="out"), duration=1).add()
```

### Complete Example 2: Text Animation

```python
from videocode.VideoCode import *

# Create title
title = text("Video-Code", fontSize=72, color=WHITE)
title.setPosition(SW*0.5, SH*0.3)

# Fade in
title.apply(fade(type="in"), duration=1).add()

# Stay visible
title.add(duration=2)

# Fade out
title.apply(fade(type="out"), duration=1).add()
```

### Complete Example 3: Image Slideshow

```python
from videocode.VideoCode import *

images = ["img1.jpg", "img2.jpg", "img3.jpg"]

for img_path in images:
    img = image(img_path)
    
    # Fade in
    img.apply(fade(type="in"), duration=0.5).add()
    
    # Show
    img.add(duration=2)
    
    # Fade out
    img.apply(fade(type="out"), duration=0.5).add()
```

## See Also

- [User Documentation](user.md)
- [Developer Documentation](../dev/dev.md)
- [Contributing Guide](../../CONTRIBUTING.md)
- [Adding Inputs Guide](../dev/addInput.md)
- [Adding Transformations Guide](../dev/addEffect.md)
