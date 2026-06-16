// Objective-C++ translation unit — the only file allowed to import AppKit /
// QuartzCore / Metal headers.  Everything is exposed to the rest of the app
// through plain C++ functions declared in metal_surface.hpp.

#include "vulkan/MetalSurface.hpp"
#import <AppKit/AppKit.h>           // NSView
#import <QuartzCore/CAMetalLayer.h> // CAMetalLayer
#include <vulkan/vulkan_metal.h>    // VkMetalSurfaceCreateInfoEXT

// createMetalLayer
//   Qt's winId() returns a pointer to the underlying NSView on macOS.
//   We cast it back with __bridge (ARC-aware, no ownership transfer) and:
//     1. Enable layer-backed rendering on the view (wantsLayer = YES).
//     2. Create a new CAMetalLayer and size it to the view's current bounds.
//     3. Add it as a sublayer so Metal/Vulkan can draw into it directly.
//   The returned void* is a non-owning __bridge cast of the CAMetalLayer*.
void *createMetalLayer(void *nativeViewHandle) {
  NSView *view = (__bridge NSView *)nativeViewHandle;
  view.wantsLayer = YES; // Activate Core Animation backing layer.
  CAMetalLayer *layer = [CAMetalLayer layer];
  layer.frame = view.bounds;      // Match the current widget size (logical points).
  CGFloat scale = view.window ? view.window.backingScaleFactor
                               : NSScreen.mainScreen.backingScaleFactor;
  layer.contentsScale = scale;    // Physical pixels = logical * scale (2× on Retina).
  [view.layer addSublayer:layer]; // Attach below Qt's own layer.
  return (__bridge void *)layer;  // Return as opaque C pointer.
}

// createMetalSurface
//   Vulkan does not know about CAMetalLayer natively; the bridge is the
//   VK_EXT_metal_surface extension provided by MoltenVK.
//   Because extensions are not statically linked, we load the function pointer
//   at runtime via vkGetInstanceProcAddr before calling it.
VkSurfaceKHR createMetalSurface(VkInstance instance, void *metalLayer) {
  // Look up the extension entry point — returns nullptr if the extension
  // wasn't enabled when the instance was created.
  auto fn = (PFN_vkCreateMetalSurfaceEXT)vkGetInstanceProcAddr(
      instance, "vkCreateMetalSurfaceEXT");
  if (!fn)
    return VK_NULL_HANDLE;

  // Fill the Metal-specific create info struct.
  // pLayer must be a CAMetalLayer*; we cast back from void*.
  VkMetalSurfaceCreateInfoEXT ci{};
  ci.sType = VK_STRUCTURE_TYPE_METAL_SURFACE_CREATE_INFO_EXT;
  ci.pLayer = (__bridge CAMetalLayer *)metalLayer;

  VkSurfaceKHR surface = VK_NULL_HANDLE;
  fn(instance, &ci, nullptr, &surface);
  return surface;
}
