// Non-Apple stub for vulkan/MetalSurface.hpp.
//
// The real implementations (src/vulkan/MetalSurface.mm) are Objective-C++
// and only compiled on Apple (see CMakeLists.txt). VulkanWidget.cpp calls
// these functions unconditionally on every platform, so non-Apple builds
// need a no-op definition to link — the Vulkan preview window is currently
// Metal-only and not yet ported to Linux/Windows surfaces.

#include "vulkan/MetalSurface.hpp"

void* createMetalLayer(void*) {
    return nullptr;
}

VkSurfaceKHR createMetalSurface(VkInstance, void*) {
    return VK_NULL_HANDLE;
}
