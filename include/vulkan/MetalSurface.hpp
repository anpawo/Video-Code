#pragma once
#include <vulkan/vulkan.h>

// This header exposes two plain C++ functions that bridge macOS-specific
// Metal/Objective-C types to the rest of the codebase.
//
// The implementations live in metal_surface.mm (Objective-C++) so that
// AppKit / QuartzCore headers never leak into regular .cpp translation units.

// createMetalLayer
//   Takes the raw NSView* that Qt gives us as a WId (native window handle)
//   and attaches a CAMetalLayer sub-layer to it.  The layer is the drawable
//   surface that both Metal and Vulkan (via MoltenVK) render into.
//   Returns a void* that actually holds a CAMetalLayer* — kept opaque here
//   so Objective-C types don't infect C++ headers.
void* createMetalLayer(void* nativeViewHandle);

// createMetalSurface
//   Wraps a CAMetalLayer* in a Vulkan VkSurfaceKHR so that Vulkan can
//   present rendered frames to the screen through MoltenVK.
//   Dynamically loads vkCreateMetalSurfaceEXT at runtime (it is a Vulkan
//   extension, not part of the core loader).
//   Returns VK_NULL_HANDLE on failure.
VkSurfaceKHR createMetalSurface(VkInstance instance, void* metalLayer);
