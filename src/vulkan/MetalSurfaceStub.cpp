// vulkan/MetalSurface.hpp, off Apple.
//
// MetalSurface.mm is Objective-C++ and CMakeLists.txt compiles it on Apple
// only; Linux presents through XCB and never reaches these two calls
// (VulkanWidget.cpp keeps them behind __APPLE__). They exist so the link
// resolves. Nothing is ported to Windows.

#include "vulkan/MetalSurface.hpp"

void* createMetalLayer(void*)
{
    return nullptr;
}

VkSurfaceKHR createMetalSurface(VkInstance, void*)
{
    return VK_NULL_HANDLE;
}
