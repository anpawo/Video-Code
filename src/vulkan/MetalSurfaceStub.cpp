// Non-Apple stub for vulkan/MetalSurface.hpp.
//
// The real implementations (src/vulkan/MetalSurface.mm) are Objective-C++ and
// only compiled on Apple (see CMakeLists.txt). On Linux the preview window
// uses an XCB surface instead (VulkanWidget.cpp guards the Metal calls behind
// __APPLE__), so these symbols are never called there — these no-op
// definitions just keep the link satisfied. Windows surfaces are not ported.

#include "vulkan/MetalSurface.hpp"

void* createMetalLayer(void*)
{
    return nullptr;
}

VkSurfaceKHR createMetalSurface(VkInstance, void*)
{
    return VK_NULL_HANDLE;
}
