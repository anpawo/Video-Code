"""Example usage of the Video-Code plugin system.

This script demonstrates how to use both transformation and input plugins.
"""

from videocode import *
from videocode.plugin import loadAllPlugins

# Load all available plugins
num_transforms, num_inputs = loadAllPlugins()
print(f"Loaded {num_transforms} transformation plugins and {num_inputs} input plugins")

# Note: To actually use plugins, they must be compiled first:
# 1. Build the C++ plugins: cd build && make
# 2. Compile Python plugins to .so (optional, can use .py directly for testing)

# Example 1: Using the Gradient input plugin
# This would require the plugin to be properly compiled and loaded
# from videocode.plugin import Gradient
# gradient = Gradient(color1=RED, color2=BLUE, direction="horizontal")
# gradient.add(duration=3)

# Example 2: Using the Blur transformation plugin
# from videocode.plugin import Blur
# circle().apply(Blur(kernel_size=15, sigma=5.0)).add()

# For now, let's show a working example with built-in inputs
# that demonstrates the plugin architecture pattern

print("\n=== Plugin System Demo ===")
print("The plugin system is now installed and ready to use.")
print("\nTo create your own plugin:")
print("1. Create a directory in plugins/transformations/ or plugins/inputs/")
print("2. Add plugin.json, <name>_plugin.py, and <name>_cpp.cpp")
print("3. Build with: cd build && cmake .. && make")
print("4. Load plugins with: from videocode.plugin import loadAllPlugins")
print("\nSee plugins/README.md for detailed instructions.")

# Traditional Video-Code example (not using plugins)
Global.config(1920, 1080, 30, "plugin_demo.mp4")

circle1 = circle(radius=100, color=RED).setPosition(960, 540)
circle1.apply(fade(), duration=1)
circle1.add(duration=2)

rectangle1 = rectangle(width=200, height=150, color=BLUE).setPosition(500, 300)
rectangle1.add(duration=2)

end()
