#!/bin/bash
# Build script for Video-Code plugins

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BUILD_DIR="$PROJECT_ROOT/build"

echo "==================================="
echo "Video-Code Plugin Builder"
echo "==================================="
echo ""

# Check if build directory exists
if [ ! -d "$BUILD_DIR" ]; then
    echo "Build directory not found. Creating..."
    mkdir -p "$BUILD_DIR"
fi

# Parse arguments
BUILD_ALL=false
BUILD_TRANSFORMATIONS=false
BUILD_INPUTS=false
CLEAN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --all|-a)
            BUILD_ALL=true
            shift
            ;;
        --transformations|-t)
            BUILD_TRANSFORMATIONS=true
            shift
            ;;
        --inputs|-i)
            BUILD_INPUTS=true
            shift
            ;;
        --clean|-c)
            CLEAN=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -a, --all              Build all plugins"
            echo "  -t, --transformations  Build transformation plugins only"
            echo "  -i, --inputs           Build input plugins only"
            echo "  -c, --clean            Clean build directory first"
            echo "  -h, --help             Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 --all              # Build all plugins"
            echo "  $0 --transformations  # Build transformation plugins"
            echo "  $0 --clean --all      # Clean and rebuild all"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Default to building all if no specific option provided
if [ "$BUILD_TRANSFORMATIONS" = false ] && [ "$BUILD_INPUTS" = false ]; then
    BUILD_ALL=true
fi

# Clean if requested
if [ "$CLEAN" = true ]; then
    echo "Cleaning build directory..."
    rm -rf "$BUILD_DIR"/*
    echo "Done."
    echo ""
fi

# Navigate to build directory
cd "$BUILD_DIR"

# Configure CMake if needed
if [ ! -f "$BUILD_DIR/Makefile" ] && [ ! -f "$BUILD_DIR/build.ninja" ]; then
    echo "Configuring CMake..."
    cmake .. || {
        echo "Error: CMake configuration failed"
        exit 1
    }
    echo ""
fi

# Build plugins
echo "Building plugins..."
echo ""

if [ "$BUILD_ALL" = true ]; then
    echo "Building all plugins..."
    make || {
        echo "Error: Build failed"
        exit 1
    }
elif [ "$BUILD_TRANSFORMATIONS" = true ]; then
    echo "Building transformation plugins..."
    # Build specific targets
    for plugin in blur; do
        make "${plugin}_cpp" || {
            echo "Error: Failed to build $plugin"
            exit 1
        }
    done
elif [ "$BUILD_INPUTS" = true ]; then
    echo "Building input plugins..."
    for plugin in gradient; do
        make "${plugin}_cpp" || {
            echo "Error: Failed to build $plugin"
            exit 1
        }
    done
fi

echo ""
echo "==================================="
echo "Plugin build completed successfully!"
echo "==================================="
echo ""

# List built plugins
echo "Built plugins:"
echo ""

if [ "$BUILD_ALL" = true ] || [ "$BUILD_TRANSFORMATIONS" = true ]; then
    echo "Transformations:"
    for plugin_dir in "$PROJECT_ROOT/plugins/transformations"/*; do
        if [ -d "$plugin_dir" ]; then
            plugin_name=$(basename "$plugin_dir")
            if [ -f "$plugin_dir/${plugin_name}_cpp.so" ]; then
                echo "  ✓ $plugin_name"
            else
                echo "  ✗ $plugin_name (not built)"
            fi
        fi
    done
    echo ""
fi

if [ "$BUILD_ALL" = true ] || [ "$BUILD_INPUTS" = true ]; then
    echo "Inputs:"
    for plugin_dir in "$PROJECT_ROOT/plugins/inputs"/*; do
        if [ -d "$plugin_dir" ]; then
            plugin_name=$(basename "$plugin_dir")
            if [ -f "$plugin_dir/${plugin_name}_cpp.so" ]; then
                echo "  ✓ $plugin_name"
            else
                echo "  ✗ $plugin_name (not built)"
            fi
        fi
    done
    echo ""
fi

echo "To use plugins in your scripts:"
echo "  from videocode.plugin import loadAllPlugins"
echo "  loadAllPlugins()"
echo ""
