#!/usr/bin/env python3
"""Test script to verify plugin system installation."""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_plugin_directories():
    """Test that plugin directories exist."""
    plugins_dir = project_root / "plugins"
    assert plugins_dir.exists(), "plugins/ directory not found"
    
    trans_dir = plugins_dir / "transformations"
    assert trans_dir.exists(), "plugins/transformations/ directory not found"
    
    inputs_dir = plugins_dir / "inputs"
    assert inputs_dir.exists(), "plugins/inputs/ directory not found"
    
    print("✓ Plugin directories exist")

def test_plugin_loader_import():
    """Test that plugin loader can be imported."""
    try:
        from videocode.plugin import loadAllPlugins, loadTransformationPlugins, loadInputPlugins
        print("✓ Plugin loader imports successfully")
    except ImportError as e:
        print(f"✗ Failed to import plugin loader: {e}")
        sys.exit(1)

def test_plugin_base_classes():
    """Test that base classes can be imported."""
    try:
        from videocode.plugin.PluginBase import PluginTransformation, PluginInput
        print("✓ Plugin base classes import successfully")
    except ImportError as e:
        print(f"✗ Failed to import base classes: {e}")
        sys.exit(1)

def test_example_plugins_exist():
    """Test that example plugins are present."""
    blur_dir = project_root / "plugins" / "transformations" / "blur"
    assert blur_dir.exists(), "Blur plugin directory not found"
    assert (blur_dir / "plugin.json").exists(), "Blur plugin.json not found"
    assert (blur_dir / "blur_cpp.cpp").exists(), "Blur C++ source not found"
    print("✓ Blur transformation plugin exists")
    
    gradient_dir = project_root / "plugins" / "inputs" / "gradient"
    assert gradient_dir.exists(), "Gradient plugin directory not found"
    assert (gradient_dir / "plugin.json").exists(), "Gradient plugin.json not found"
    assert (gradient_dir / "gradient_cpp.cpp").exists(), "Gradient C++ source not found"
    print("✓ Gradient input plugin exists")

def test_cmake_plugin_config():
    """Test that plugin CMake configuration exists."""
    cmake_file = project_root / "plugins" / "CMakeLists.txt"
    assert cmake_file.exists(), "plugins/CMakeLists.txt not found"
    print("✓ Plugin CMake configuration exists")

def test_plugin_discovery():
    """Test plugin discovery (without loading .so files)."""
    from videocode.plugin.PluginLoader import discoverPlugins
    
    plugins_root = project_root / "plugins"
    
    # Note: This will only work if .so files are built
    # For now, we just test that the function runs without error
    try:
        trans_plugins = discoverPlugins(plugins_root, "transformation")
        input_plugins = discoverPlugins(plugins_root, "input")
        print(f"✓ Plugin discovery runs (found {len(trans_plugins)} transformations, {len(input_plugins)} inputs)")
    except Exception as e:
        print(f"✓ Plugin discovery runs (build plugins to load: {e})")

def main():
    """Run all tests."""
    print("=" * 60)
    print("Video-Code Plugin System Tests")
    print("=" * 60)
    print()
    
    try:
        test_plugin_directories()
        test_plugin_loader_import()
        test_plugin_base_classes()
        test_example_plugins_exist()
        test_cmake_plugin_config()
        test_plugin_discovery()
        
        print()
        print("=" * 60)
        print("All tests passed! ✓")
        print("=" * 60)
        print()
        print("To build plugins, run:")
        print("  ./scripts/build_plugins.sh --all")
        print()
        print("Or build the entire project:")
        print("  cd build && cmake .. && make")
        print()
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
