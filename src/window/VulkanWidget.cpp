/*
** EPITECH PROJECT, 2026
** video-code
** File description:
** VulkanWidget
*/

// Core Vulkan rendering implementation.
// Owns the entire GPU pipeline: from instance creation to per-frame present.
// Every method is roughly in the order it is called during startup.

#include "window/VulkanWidget.hpp"

#if defined(__APPLE__)
#include <vulkan/vulkan_metal.h>
#elif defined(__linux__)
// Linux presents through an XCB surface. xcb/xcb.h must come before
// vulkan_xcb.h — it provides the xcb_connection_t / xcb_window_t types the
// VkXcbSurfaceCreateInfoKHR struct refers to.
#include <xcb/xcb.h>

#include <vulkan/vulkan_xcb.h>

#include <QGuiApplication>
#include <QtGui/qguiapplication_platform.h> // QNativeInterface::QX11Application
#endif

#include <QDebug>
#include <QResizeEvent>
#include <QWindow>
#include <algorithm>
#include <array>
#include <chrono>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <sstream>

#include "utils/Logger.hpp"
#include "vulkan/EffectResolver.hpp"
#include "vulkan/LutAtlas.hpp"
#if defined(__APPLE__)
#include "vulkan/MetalSurface.hpp" // CAMetalLayer bridge (macOS only)
#endif
#include "vulkan/ShaderCompiler.hpp" // Runtime GLSL → SPIR-V via glslang
#include "vulkan/Vertex.hpp"

// ---------------------------------------------------------------------------
// loadEffectShader — read GLSL from assets/shaders/{folder}/{file}
// ---------------------------------------------------------------------------

static std::string loadEffectShader(const std::string& folder, const std::string& file)
{
    std::string   path = std::string(SHADER_DIR) + "/" + folder + "/" + file;
    std::ifstream f(path);
    if (!f.is_open()) return {};
    std::ostringstream ss;
    ss << f.rdbuf();
    return ss.str();
}

struct EffectPC
{
    float texelX;
    float texelY;
    float p[8];
};

static void effectBarrier(VkCommandBuffer cb, VkPipelineStageFlags srcStage, VkPipelineStageFlags dstStage, VkImage image, VkAccessFlags srcAccess, VkAccessFlags dstAccess, VkImageLayout oldLayout = VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL, VkImageLayout newLayout = VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL)
{
    VkImageMemoryBarrier b{};
    b.sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER;
    b.srcAccessMask = srcAccess;
    b.dstAccessMask = dstAccess;
    b.oldLayout = oldLayout;
    b.newLayout = newLayout;
    b.srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
    b.dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
    b.image = image;
    b.subresourceRange = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1};
    vkCmdPipelineBarrier(cb, srcStage, dstStage, 0, 0, nullptr, 0, nullptr, 1, &b);
}

static void effectBarrier2(VkCommandBuffer cb, VkImage readImg, VkImage writeImg)
{
    VkImageMemoryBarrier bs[2]{};
    bs[0].sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER;
    bs[0].srcAccessMask = VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT;
    bs[0].dstAccessMask = VK_ACCESS_SHADER_READ_BIT;
    bs[0].oldLayout = VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL;
    bs[0].newLayout = VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL;
    bs[0].srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
    bs[0].dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
    bs[0].image = readImg;
    bs[0].subresourceRange = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1};
    bs[1].sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER;
    bs[1].srcAccessMask = VK_ACCESS_SHADER_READ_BIT;
    bs[1].dstAccessMask = VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT;
    bs[1].oldLayout = VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL;
    bs[1].newLayout = VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL;
    bs[1].srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
    bs[1].dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
    bs[1].image = writeImg;
    bs[1].subresourceRange = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1};
    vkCmdPipelineBarrier(cb, VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT | VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT, VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT | VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT, 0, 0, nullptr, 0, nullptr, 2, bs);
}

// ============================================================================
// loadShaderSource
//   Reads a GLSL file from assets/shaders/quadraticBezier/ at runtime.
// ============================================================================

static std::string loadShaderSource(const std::string& filename)
{
    std::string   path = std::string(SHADER_DIR) + "/quadraticBezier/" + filename;
    std::ifstream f(path);
    if (!f.is_open()) {
        qWarning("Failed to open shader: %s", path.c_str());
        return {};
    }
    std::ostringstream ss;
    ss << f.rdbuf();
    return ss.str();
}

// ============================================================================
// Constructor / Destructor
// ============================================================================

VC::VulkanWidget::VulkanWidget(QWidget* parent)
    : QWidget(parent)
{
    // Tell Qt to allocate a real native OS window handle.
    // Without this, winId() may not be backed by a real window and
    // createMetalLayer() would fail.
    setAttribute(Qt::WA_NativeWindow);

    // Prevent Qt from compositing this widget; our Vulkan swapchain presents
    // directly to the display, bypassing Qt's paint system.
    setAttribute(Qt::WA_PaintOnScreen);

    // Disable Qt's automatic background fill (would overwrite Vulkan output).
    setAttribute(Qt::WA_NoSystemBackground);

    // Default geometry: full-screen quad made of two triangles.
    // Clip-space: X,Y ∈ [-1,1].  UV: U,V ∈ [0,1].
    //
    //   (-1,-1) ─── (1,-1)
    //      │  ╲  tri1  │
    //      │    ╲      │
    //      │  tri2 ╲   │
    //   (-1, 1) ─── (1, 1)
    m_vertices = {
        Vertex{{-1.0f, -1.0f}, {0.0f, 0.0f}, {0, 0, 0, 0}, {0, 0, 0, 0}}, // bottom-left
        Vertex{{1.0f, -1.0f}, {1.0f, 0.0f}, {0, 0, 0, 0}, {0, 0, 0, 0}},  // bottom-right
        Vertex{{1.0f, 1.0f}, {1.0f, 1.0f}, {0, 0, 0, 0}, {0, 0, 0, 0}},   // top-right
        Vertex{{-1.0f, -1.0f}, {0.0f, 0.0f}, {0, 0, 0, 0}, {0, 0, 0, 0}}, // bottom-left (tri 2)
        Vertex{{1.0f, 1.0f}, {1.0f, 1.0f}, {0, 0, 0, 0}, {0, 0, 0, 0}},   // top-right
        Vertex{{-1.0f, 1.0f}, {0.0f, 1.0f}, {0, 0, 0, 0}, {0, 0, 0, 0}},  // top-left
    };
}

VC::VulkanWidget::~VulkanWidget()
{
    cleanup();
}

// ============================================================================
// Public API
// ============================================================================

void VC::VulkanWidget::setMeshes(const std::vector<Mesh>& meshes)
{
    m_vertices.clear();
    m_indices.clear();
    m_meshes = meshes;
    m_meshDrawInfos.clear();
    m_effectMeshIndices.clear();
    m_inputIndexToMeshPos.clear();
    m_matteSourceMeshPositions.clear();
    m_adjustmentMeshPositions.clear();

    // Input identity + matte-source marking (see the headless renderer's
    // setMeshes for the rationale — both renderers stay mirrored).
    for (size_t mi = 0; mi < meshes.size(); ++mi)
        if (meshes[mi].inputIndex >= 0)
            m_inputIndexToMeshPos[meshes[mi].inputIndex] = mi;

    for (const auto& mesh : meshes) {
        if (mesh.matteSourceInputIndex < 0) continue;
        auto it = m_inputIndexToMeshPos.find(mesh.matteSourceInputIndex);
        if (it != m_inputIndexToMeshPos.end())
            m_matteSourceMeshPositions.insert(it->second);
    }

    for (size_t mi = 0; mi < meshes.size(); ++mi) {
        const auto& mesh = meshes[mi];

        MeshDrawInfo info{};
        info.firstIndex = static_cast<uint32_t>(m_indices.size());
        info.indexCount = static_cast<uint32_t>(mesh.indices.size());

        uint32_t vertexOffset = static_cast<uint32_t>(m_vertices.size());
        m_vertices.insert(m_vertices.end(), mesh.vertices.begin(), mesh.vertices.end());
        for (auto idx : mesh.indices)
            m_indices.push_back(vertexOffset + idx);
        m_meshDrawInfos.push_back(info);

        // Isolate meshes with a GLSL effect chain, matte consumers, matte
        // sources, AND adjustment layers (a zero-effect isolated mesh still
        // Passthrough-flushes into its slot — an effect-less adjustment layer
        // thus recomposites its below-range unchanged, an identity grade).
        if (!mesh.effects.empty() || mesh.matteSourceInputIndex >= 0 || m_matteSourceMeshPositions.count(mi) || mesh.isAdjustmentLayer)
            m_effectMeshIndices.push_back(mi);

        if (mesh.isAdjustmentLayer)
            m_adjustmentMeshPositions.push_back(mi);
    }

    // Object-space → absolute-UV param patching (Crop/Vignette bbox,
    // LightSweep group union) — shared with the headless renderer, see
    // EffectResolver.hpp.
    resolveEffectParams(m_meshes);

    m_geomDirty = true;

    if (!m_effectMeshIndices.empty())
        ensureEffectResultCapacity(m_effectMeshIndices.size());

    size_t matteConsumers = 0;
    for (const auto& mesh : meshes)
        if (mesh.matteSourceInputIndex >= 0 && m_inputIndexToMeshPos.count(mesh.matteSourceInputIndex))
            ++matteConsumers;
    if (matteConsumers)
        ensureMatteSetCapacity(matteConsumers);

    // One LUT descriptor set per lut combine this frame (any mesh, any lut
    // effect) — each needs its own set (can't re-point mid-command-buffer).
    size_t lutCombines = 0;
    for (const auto& mesh : meshes)
        for (const auto& eff : mesh.effects)
            if (!eff.strParam.empty() && eff.name == "Lut")
                ++lutCombines;
    if (lutCombines)
        ensureLutSetCapacity(lutCombines);
}

void VC::VulkanWidget::setFrameCallback(std::function<std::vector<Mesh>()> cb)
{
    m_frameCallback = std::move(cb);
}

bool VC::VulkanWidget::event(QEvent* e)
{
    // UpdateRequest on the widget itself (fallback path when QWindow is absent).
    if (e->type() == QEvent::UpdateRequest) {
        render();
        return true;
    }
    return QWidget::event(e);
}

bool VC::VulkanWidget::eventFilter(QObject* obj, QEvent* e)
{
    // Forward UpdateRequest from the underlying QWindow into our render loop.
    if (obj == windowHandle() && e->type() == QEvent::UpdateRequest) {
        render();
        return true;
    }
    return QWidget::eventFilter(obj, e);
}

// ============================================================================
// init() — master initialisation sequence
//   Must be called after show() so the native window handle exists.
//   Steps run in strict dependency order.
// ============================================================================

bool VC::VulkanWidget::init()
{
    // ── Startup timing ────────────────────────────────────────────────────────
    // Always-on: printed once at startup so we can see where time goes without
    // a special debug build.  Each step resets _t_step.
    using Clock = std::chrono::high_resolution_clock;
    using Ms = std::chrono::duration<double, std::milli>;
    auto _t_init_start = Clock::now();
    auto _t_step = Clock::now();
    auto _step = [&]([[maybe_unused]] const char* name, bool ok = true) -> bool {
        [[maybe_unused]] double ms = std::chrono::duration_cast<Ms>(Clock::now() - _t_step).count();
        VC_SLOG(std::format("[startup] {:35s} {:7.1f}ms{}\n", name, ms, ok ? "" : "  ← FAILED"));
        _t_step = Clock::now();
        return ok;
    };

#if defined(__APPLE__)
    // Attach a CAMetalLayer to the Qt native window (macOS).
    WId handle = winId();
    m_metalLayer = createMetalLayer(reinterpret_cast<void*>(handle));
    _step("createMetalLayer");
#endif

    if (!createInstance()) {
        _step("createInstance", false);
        qWarning("createInstance failed");
        return false;
    }
    _step("createInstance");

    if (!createSurface()) {
        _step("createSurface", false);
        qWarning("createSurface failed");
        return false;
    }
    _step("createSurface");

    if (!pickPhysicalDevice()) {
        _step("pickPhysicalDevice", false);
        qWarning("pickPhysicalDevice failed");
        return false;
    }
    _step("pickPhysicalDevice");

    if (!createDevice()) {
        _step("createDevice", false);
        qWarning("createDevice failed");
        return false;
    }
    _step("createDevice");

    if (!createSwapchain()) {
        _step("createSwapchain", false);
        qWarning("createSwapchain failed");
        return false;
    }
    _step("createSwapchain");

    if (!createSsaaResources()) {
        _step("createSsaaResources", false);
        qWarning("createSsaaResources failed");
        return false;
    }
    _step("createSsaaResources");

    if (!createReadbackResources()) {
        _step("createReadbackResources", false);
        qWarning("createReadbackResources failed");
        return false;
    }
    _step("createReadbackResources");

    if (!createRenderPass()) {
        _step("createRenderPass", false);
        qWarning("createRenderPass failed");
        return false;
    }
    _step("createRenderPass");

    if (!createUniformBuffer()) {
        _step("createUniformBuffer", false);
        qWarning("createUniformBuffer failed");
        return false;
    }
    _step("createUniformBuffer");

    if (!createDescriptorSet()) {
        _step("createDescriptorSet", false);
        qWarning("createDescriptorSet failed");
        return false;
    }
    _step("createDescriptorSet");

    if (!createPipeline()) {
        _step("createPipeline [main vert+frag]", false);
        qWarning("createPipeline failed");
        return false;
    }
    _step("createPipeline [main vert+frag]");

    if (!createVertexBuffer()) {
        _step("createVertexBuffer", false);
        qWarning("createVertexBuffer failed");
        return false;
    }
    _step("createVertexBuffer");

    if (!createIndexBuffer()) {
        _step("createIndexBuffer", false);
        qWarning("createIndexBuffer failed");
        return false;
    }
    _step("createIndexBuffer");

    if (!createFramebuffers()) {
        _step("createFramebuffers", false);
        qWarning("createFramebuffers failed");
        return false;
    }
    _step("createFramebuffers");

    if (!createCommandPool()) {
        _step("createCommandPool", false);
        qWarning("createCommandPool failed");
        return false;
    }
    _step("createCommandPool");

    // Upload the default 1×1 white texture now that the command pool exists.
    cv::Mat white(1, 1, CV_8UC4, cv::Scalar(255, 255, 255, 255));
    m_defaultTextureSet = uploadTexture(white);
    if (m_defaultTextureSet == VK_NULL_HANDLE) {
        _step("uploadDefaultTexture", false);
        qWarning("default texture upload failed");
        return false;
    }
    _step("uploadDefaultTexture");

    if (!createCommandBuffers()) {
        _step("createCommandBuffers", false);
        qWarning("createCommandBuffers failed");
        return false;
    }
    _step("createCommandBuffers");

    if (!createSyncObjects()) {
        _step("createSyncObjects", false);
        qWarning("createSyncObjects failed");
        return false;
    }
    _step("createSyncObjects");

    if (!createEffectResources()) {
        _step("createEffectResources [all effect shaders]", false);
        qWarning("createEffectResources failed");
        return false;
    }
    _step("createEffectResources [all effect shaders]");

    [[maybe_unused]] double total_ms = std::chrono::duration_cast<Ms>(Clock::now() - _t_init_start).count();
    VC_SLOG(std::format("[startup] === VulkanWidget::init() total: {:.1f}ms ===\n", total_ms));

    m_initialized = true;
    qDebug() << "Vulkan initialized successfully";
    // qDebug() << "VulkanWidget geometry:" << geometry();
    // qDebug() << "VulkanWidget size:" << size();
    // qDebug() << "Swapchain extent:" << m_swapExtent.width << "x" << m_swapExtent.height;
    // qDebug() << "Parent window size:" << (parentWidget() ? parentWidget()->size() : QSize{});

    // Install an event filter on the underlying QWindow so that UpdateRequest
    // events (delivered by windowHandle()->requestUpdate()) are forwarded here.
    if (windowHandle()) {
        windowHandle()->installEventFilter(this);
    }
    // Kick off the render loop.
    if (windowHandle()) {
        windowHandle()->requestUpdate();
    } else {
        update();
    }
    return true;
}

// ============================================================================
// Qt event overrides
// ============================================================================

void VC::VulkanWidget::paintEvent(QPaintEvent*) { render(); }

void VC::VulkanWidget::resizeEvent(QResizeEvent*)
{
    if (m_initialized) {
        recreateSwapchain();
    }
}

// ============================================================================
// Step 1: createInstance
//   VkInstance is the root of the Vulkan object tree.
//   VK_EXT_metal_surface wraps a CAMetalLayer as a VkSurfaceKHR on macOS.
// ============================================================================

bool VC::VulkanWidget::createInstance()
{
    VkApplicationInfo appInfo{};
    appInfo.sType = VK_STRUCTURE_TYPE_APPLICATION_INFO;
    appInfo.pApplicationName = "video-code";
    appInfo.apiVersion = VK_API_VERSION_1_0;

    std::vector<const char*> extensions = {
        VK_KHR_SURFACE_EXTENSION_NAME,
#if defined(__APPLE__)
        VK_EXT_METAL_SURFACE_EXTENSION_NAME,
#elif defined(__linux__)
        VK_KHR_XCB_SURFACE_EXTENSION_NAME,
#endif
    };

    VkInstanceCreateInfo ci{};
    ci.sType = VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO;
    ci.pApplicationInfo = &appInfo;
    ci.enabledExtensionCount = (uint32_t)extensions.size();
    ci.ppEnabledExtensionNames = extensions.data();

    return vkCreateInstance(&ci, nullptr, &m_instance) == VK_SUCCESS;
}

// ============================================================================
// Step 2: createSurface
//   macOS: delegates to MetalSurface.mm (vkCreateMetalSurfaceEXT over a
//          CAMetalLayer).
//   Linux: builds a VkSurfaceKHR from the Qt widget's native XCB window.
// ============================================================================

bool VC::VulkanWidget::createSurface()
{
#if defined(__APPLE__)
    m_surface = createMetalSurface(m_instance, m_metalLayer);
#elif defined(__linux__)
    // Qt's xcb platform plugin owns the X connection; borrow it through the
    // public native interface. (Under a Wayland session we still land here via
    // XWayland, because the vcpkg Qt build ships only the xcb platform plugin.)
    auto* x11 = qApp->nativeInterface<QNativeInterface::QX11Application>();
    if (!x11) {
        qWarning("createSurface: XCB native interface unavailable (not on the xcb platform?)");
        return false;
    }
    // vkCreateXcbSurfaceKHR is an extension entry point, not guaranteed to be
    // exported by the loader at link time — resolve it dynamically (same
    // approach MetalSurface.mm uses for vkCreateMetalSurfaceEXT).
    auto createXcbSurface = reinterpret_cast<PFN_vkCreateXcbSurfaceKHR>(
        vkGetInstanceProcAddr(m_instance, "vkCreateXcbSurfaceKHR"));
    if (!createXcbSurface) {
        qWarning("createSurface: vkCreateXcbSurfaceKHR unavailable (loader built without XCB WSI?)");
        return false;
    }
    VkXcbSurfaceCreateInfoKHR ci{};
    ci.sType = VK_STRUCTURE_TYPE_XCB_SURFACE_CREATE_INFO_KHR;
    ci.connection = x11->connection();
    ci.window = static_cast<xcb_window_t>(winId()); // WA_NativeWindow realizes it
    if (createXcbSurface(m_instance, &ci, nullptr, &m_surface) != VK_SUCCESS)
        m_surface = VK_NULL_HANDLE;
#endif
    return m_surface != VK_NULL_HANDLE;
}

// ============================================================================
// Step 3: pickPhysicalDevice
//   Choose the first GPU with a queue family that supports graphics + present.
// ============================================================================

bool VC::VulkanWidget::pickPhysicalDevice()
{
    uint32_t count = 0;
    vkEnumeratePhysicalDevices(m_instance, &count, nullptr);
    std::vector<VkPhysicalDevice> devs(count);
    vkEnumeratePhysicalDevices(m_instance, &count, devs.data());

    for (auto pd : devs) {
        uint32_t qCount = 0;
        vkGetPhysicalDeviceQueueFamilyProperties(pd, &qCount, nullptr);
        std::vector<VkQueueFamilyProperties> qProps(qCount);
        vkGetPhysicalDeviceQueueFamilyProperties(pd, &qCount, qProps.data());

        for (uint32_t i = 0; i < qCount; i++) {
            VkBool32 present = false;
            vkGetPhysicalDeviceSurfaceSupportKHR(pd, i, m_surface, &present);

            if ((qProps[i].queueFlags & VK_QUEUE_GRAPHICS_BIT) && present) {
                m_physicalDevice = pd;
                m_graphicsFamily = i;

                return true;
            }
        }
    }
    return false;
}

// ============================================================================
// Step 4: createDevice
//   Create the logical VkDevice and retrieve the graphics VkQueue.
//   VK_KHR_portability_subset must be enabled *iff* the device advertises it
//   (MoltenVK on macOS does; native Linux/Windows drivers don't).
// ============================================================================

bool VC::VulkanWidget::createDevice()
{
    float priority = 1.0f;

    VkDeviceQueueCreateInfo qci{};
    qci.sType = VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO;
    qci.queueFamilyIndex = m_graphicsFamily;
    qci.queueCount = 1;
    qci.pQueuePriorities = &priority;

    std::vector<const char*> extensions = {
        VK_KHR_SWAPCHAIN_EXTENSION_NAME,
    };

    // Per the Vulkan spec, VK_KHR_portability_subset must be enabled whenever a
    // physical device exposes it — but requesting it on a device that does not
    // (every native Linux driver) makes vkCreateDevice fail. So enable it only
    // when present.
    uint32_t extCount = 0;
    vkEnumerateDeviceExtensionProperties(m_physicalDevice, nullptr, &extCount, nullptr);
    std::vector<VkExtensionProperties> available(extCount);
    vkEnumerateDeviceExtensionProperties(m_physicalDevice, nullptr, &extCount, available.data());
    for (const auto& ext : available) {
        if (std::strcmp(ext.extensionName, "VK_KHR_portability_subset") == 0) {
            extensions.push_back("VK_KHR_portability_subset");
            break;
        }
    }

    VkDeviceCreateInfo ci{};
    ci.sType = VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO;
    ci.queueCreateInfoCount = 1;
    ci.pQueueCreateInfos = &qci;
    ci.enabledExtensionCount = (uint32_t)extensions.size();
    ci.ppEnabledExtensionNames = extensions.data();
    if (vkCreateDevice(m_physicalDevice, &ci, nullptr, &m_device) != VK_SUCCESS) {
        return false;
    }

    vkGetDeviceQueue(m_device, m_graphicsFamily, 0, &m_graphicsQueue);
    return true;
}

// ============================================================================
// Step 5: createSwapchain
//   Double-buffered swapchain with FIFO (VSync) present mode.
//   Also creates a VkImageView per swapchain image.
// ============================================================================

bool VC::VulkanWidget::createSwapchain()
{
    VkSurfaceCapabilitiesKHR caps;
    vkGetPhysicalDeviceSurfaceCapabilitiesKHR(m_physicalDevice, m_surface, &caps);

    // 0xFFFFFFFF means the surface lets us choose the size freely.
    m_swapExtent = caps.currentExtent;
    if (m_swapExtent.width == 0xFFFFFFFF) {
        m_swapExtent = {(uint32_t)width(), (uint32_t)height()};
    }

    uint32_t fmtCount = 0;
    vkGetPhysicalDeviceSurfaceFormatsKHR(m_physicalDevice, m_surface, &fmtCount, nullptr);
    std::vector<VkSurfaceFormatKHR> formats(fmtCount);
    vkGetPhysicalDeviceSurfaceFormatsKHR(m_physicalDevice, m_surface, &fmtCount, formats.data());

    // Prefer B8G8R8A8_UNORM so the swapchain (and the render-pass attachments
    // that reuse m_swapFormat) match the rest of the pipeline and the headless
    // renderer, which render sRGB-encoded colors into UNORM targets. Drivers
    // differ in ordering — some list an _SRGB format first, and presenting into
    // it re-applies sRGB encoding, washing the colors out. Fall back to the
    // driver's first format only if UNORM isn't offered.
    VkSurfaceFormatKHR chosen = formats[0];
    for (const auto& f : formats) {
        if (f.format == VK_FORMAT_B8G8R8A8_UNORM) {
            chosen = f;
            break;
        }
    }
    m_swapFormat = chosen.format;

    VkSwapchainCreateInfoKHR ci{};
    ci.sType = VK_STRUCTURE_TYPE_SWAPCHAIN_CREATE_INFO_KHR;
    ci.surface = m_surface;
    ci.minImageCount = 2;
    ci.imageFormat = m_swapFormat;
    ci.imageColorSpace = chosen.colorSpace;
    ci.imageExtent = m_swapExtent;
    ci.imageArrayLayers = 1;
    ci.imageUsage = VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT | VK_IMAGE_USAGE_TRANSFER_DST_BIT;
    ci.imageSharingMode = VK_SHARING_MODE_EXCLUSIVE;
    ci.preTransform = caps.currentTransform;
    ci.compositeAlpha = VK_COMPOSITE_ALPHA_OPAQUE_BIT_KHR;
    ci.presentMode = VK_PRESENT_MODE_FIFO_KHR;
    ci.clipped = VK_TRUE;

    if (vkCreateSwapchainKHR(m_device, &ci, nullptr, &m_swapchain) != VK_SUCCESS) {
        return false;
    }

    uint32_t imgCount = 0;
    vkGetSwapchainImagesKHR(m_device, m_swapchain, &imgCount, nullptr);
    m_swapImages.resize(imgCount);
    vkGetSwapchainImagesKHR(m_device, m_swapchain, &imgCount, m_swapImages.data());

    m_swapImageViews.resize(imgCount);
    for (uint32_t i = 0; i < imgCount; i++) {
        VkImageViewCreateInfo ivci{};
        ivci.sType = VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO;
        ivci.image = m_swapImages[i];
        ivci.viewType = VK_IMAGE_VIEW_TYPE_2D;
        ivci.format = m_swapFormat;
        ivci.subresourceRange.aspectMask = VK_IMAGE_ASPECT_COLOR_BIT;
        ivci.subresourceRange.levelCount = 1;
        ivci.subresourceRange.layerCount = 1;
        vkCreateImageView(m_device, &ivci, nullptr, &m_swapImageViews[i]);
    }
    return true;
}

// ============================================================================
// Step 5b: createSsaaResources
//   Allocates a 4× offscreen image used as the render target.
//   The render pass draws here; recordCommandBuffer() blits it down to the
//   swapchain image with VK_FILTER_LINEAR for a free 16-sample box filter.
// ============================================================================

bool VC::VulkanWidget::createSsaaResources()
{
    m_ssaaExtent = m_swapExtent;

    // ── MSAA color attachment (4 samples, device-local) ──────────────────
    {
        VkImageCreateInfo ici{};
        ici.sType = VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO;
        ici.imageType = VK_IMAGE_TYPE_2D;
        ici.format = m_swapFormat;
        ici.extent = {m_swapExtent.width, m_swapExtent.height, 1};
        ici.mipLevels = 1;
        ici.arrayLayers = 1;
        ici.samples = VK_SAMPLE_COUNT_4_BIT;
        ici.tiling = VK_IMAGE_TILING_OPTIMAL;
        ici.usage = VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT;
        ici.sharingMode = VK_SHARING_MODE_EXCLUSIVE;
        ici.initialLayout = VK_IMAGE_LAYOUT_UNDEFINED;

        if (vkCreateImage(m_device, &ici, nullptr, &m_ssaaImage) != VK_SUCCESS)
            return false;

        VkMemoryRequirements memReq;
        vkGetImageMemoryRequirements(m_device, m_ssaaImage, &memReq);

        VkMemoryAllocateInfo ai{};
        ai.sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
        ai.allocationSize = memReq.size;
        ai.memoryTypeIndex = findMemoryType(memReq.memoryTypeBits, VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT);

        if (vkAllocateMemory(m_device, &ai, nullptr, &m_ssaaMemory) != VK_SUCCESS)
            return false;
        vkBindImageMemory(m_device, m_ssaaImage, m_ssaaMemory, 0);

        VkImageViewCreateInfo ivci{};
        ivci.sType = VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO;
        ivci.image = m_ssaaImage;
        ivci.viewType = VK_IMAGE_VIEW_TYPE_2D;
        ivci.format = m_swapFormat;
        ivci.subresourceRange = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1};

        if (vkCreateImageView(m_device, &ivci, nullptr, &m_ssaaImageView) != VK_SUCCESS)
            return false;
    }

    // ── Resolve image (1 sample, TRANSFER_SRC for readFrame) ─────────────
    {
        VkImageCreateInfo ici{};
        ici.sType = VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO;
        ici.imageType = VK_IMAGE_TYPE_2D;
        ici.format = m_swapFormat;
        ici.extent = {m_swapExtent.width, m_swapExtent.height, 1};
        ici.mipLevels = 1;
        ici.arrayLayers = 1;
        ici.samples = VK_SAMPLE_COUNT_1_BIT;
        ici.tiling = VK_IMAGE_TILING_OPTIMAL;
        ici.usage = VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT | VK_IMAGE_USAGE_TRANSFER_SRC_BIT;
        ici.sharingMode = VK_SHARING_MODE_EXCLUSIVE;
        ici.initialLayout = VK_IMAGE_LAYOUT_UNDEFINED;

        if (vkCreateImage(m_device, &ici, nullptr, &m_resolveImage) != VK_SUCCESS)
            return false;

        VkMemoryRequirements memReq;
        vkGetImageMemoryRequirements(m_device, m_resolveImage, &memReq);

        VkMemoryAllocateInfo ai{};
        ai.sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
        ai.allocationSize = memReq.size;
        ai.memoryTypeIndex = findMemoryType(memReq.memoryTypeBits, VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT);

        if (vkAllocateMemory(m_device, &ai, nullptr, &m_resolveMemory) != VK_SUCCESS)
            return false;
        vkBindImageMemory(m_device, m_resolveImage, m_resolveMemory, 0);

        VkImageViewCreateInfo ivci{};
        ivci.sType = VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO;
        ivci.image = m_resolveImage;
        ivci.viewType = VK_IMAGE_VIEW_TYPE_2D;
        ivci.format = m_swapFormat;
        ivci.subresourceRange = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1};

        return vkCreateImageView(m_device, &ivci, nullptr, &m_resolveImageView) == VK_SUCCESS;
    }
}

void VC::VulkanWidget::destroySsaaResources()
{
    if (m_resolveImageView != VK_NULL_HANDLE) {
        vkDestroyImageView(m_device, m_resolveImageView, nullptr);
        m_resolveImageView = VK_NULL_HANDLE;
    }
    if (m_resolveImage != VK_NULL_HANDLE) {
        vkDestroyImage(m_device, m_resolveImage, nullptr);
        m_resolveImage = VK_NULL_HANDLE;
    }
    if (m_resolveMemory != VK_NULL_HANDLE) {
        vkFreeMemory(m_device, m_resolveMemory, nullptr);
        m_resolveMemory = VK_NULL_HANDLE;
    }
    if (m_ssaaImageView != VK_NULL_HANDLE) {
        vkDestroyImageView(m_device, m_ssaaImageView, nullptr);
        m_ssaaImageView = VK_NULL_HANDLE;
    }
    if (m_ssaaImage != VK_NULL_HANDLE) {
        vkDestroyImage(m_device, m_ssaaImage, nullptr);
        m_ssaaImage = VK_NULL_HANDLE;
    }
    if (m_ssaaMemory != VK_NULL_HANDLE) {
        vkFreeMemory(m_device, m_ssaaMemory, nullptr);
        m_ssaaMemory = VK_NULL_HANDLE;
    }
}

// ============================================================================
// createReadbackResources / destroyReadbackResources
//   A linear, host-visible image at swapchain resolution used to copy the
//   rendered SSAA blit result back to CPU memory for video export.
// ============================================================================

bool VC::VulkanWidget::createReadbackResources()
{
    VkImageCreateInfo ici{};
    ici.sType = VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO;
    ici.imageType = VK_IMAGE_TYPE_2D;
    ici.format = VK_FORMAT_B8G8R8A8_UNORM; // matches OpenCV BGRA layout
    ici.extent = {m_swapExtent.width, m_swapExtent.height, 1};
    ici.mipLevels = 1;
    ici.arrayLayers = 1;
    ici.samples = VK_SAMPLE_COUNT_1_BIT;
    ici.tiling = VK_IMAGE_TILING_LINEAR;
    ici.usage = VK_IMAGE_USAGE_TRANSFER_DST_BIT;
    ici.sharingMode = VK_SHARING_MODE_EXCLUSIVE;
    ici.initialLayout = VK_IMAGE_LAYOUT_UNDEFINED;

    if (vkCreateImage(m_device, &ici, nullptr, &m_readbackImage) != VK_SUCCESS) {
        return false;
    }

    VkMemoryRequirements memReq;
    vkGetImageMemoryRequirements(m_device, m_readbackImage, &memReq);

    VkMemoryAllocateInfo ai{};
    ai.sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
    ai.allocationSize = memReq.size;
    ai.memoryTypeIndex = findMemoryType(
        memReq.memoryTypeBits,
        VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT
    );

    if (vkAllocateMemory(m_device, &ai, nullptr, &m_readbackMemory) != VK_SUCCESS) {
        return false;
    }
    vkBindImageMemory(m_device, m_readbackImage, m_readbackMemory, 0);
    return true;
}

void VC::VulkanWidget::destroyReadbackResources()
{
    if (m_readbackImage != VK_NULL_HANDLE) {
        vkDestroyImage(m_device, m_readbackImage, nullptr);
        m_readbackImage = VK_NULL_HANDLE;
    }
    if (m_readbackMemory != VK_NULL_HANDLE) {
        vkFreeMemory(m_device, m_readbackMemory, nullptr);
        m_readbackMemory = VK_NULL_HANDLE;
    }
}

// ============================================================================
// Step 6: createRenderPass
//   Single colour attachment: clear to black on load, store for blit to swapchain.
// ============================================================================

bool VC::VulkanWidget::createRenderPass()
{
    // Attachment 0: MSAA color — cleared each frame, samples discarded after resolve.
    VkAttachmentDescription msaaAttachment{};
    msaaAttachment.format = m_swapFormat;
    msaaAttachment.samples = VK_SAMPLE_COUNT_4_BIT;
    msaaAttachment.loadOp = VK_ATTACHMENT_LOAD_OP_CLEAR;
    msaaAttachment.storeOp = VK_ATTACHMENT_STORE_OP_DONT_CARE;
    msaaAttachment.stencilLoadOp = VK_ATTACHMENT_LOAD_OP_DONT_CARE;
    msaaAttachment.stencilStoreOp = VK_ATTACHMENT_STORE_OP_DONT_CARE;
    msaaAttachment.initialLayout = VK_IMAGE_LAYOUT_UNDEFINED;
    msaaAttachment.finalLayout = VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL;

    // Attachment 1: Resolve target — render pass writes resolved pixels here.
    // finalLayout = TRANSFER_SRC_OPTIMAL so readFrame can blit straight from it;
    // for live rendering we add one barrier after the pass to go to PRESENT_SRC_KHR.
    VkAttachmentDescription resolveAttachment{};
    resolveAttachment.format = m_swapFormat;
    resolveAttachment.samples = VK_SAMPLE_COUNT_1_BIT;
    resolveAttachment.loadOp = VK_ATTACHMENT_LOAD_OP_DONT_CARE;
    resolveAttachment.storeOp = VK_ATTACHMENT_STORE_OP_STORE;
    resolveAttachment.stencilLoadOp = VK_ATTACHMENT_LOAD_OP_DONT_CARE;
    resolveAttachment.stencilStoreOp = VK_ATTACHMENT_STORE_OP_DONT_CARE;
    resolveAttachment.initialLayout = VK_IMAGE_LAYOUT_UNDEFINED;
    resolveAttachment.finalLayout = VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL;

    VkAttachmentReference colorRef{};
    colorRef.attachment = 0;
    colorRef.layout = VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL;

    VkAttachmentReference resolveRef{};
    resolveRef.attachment = 1;
    resolveRef.layout = VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL;

    VkSubpassDescription subpass{};
    subpass.pipelineBindPoint = VK_PIPELINE_BIND_POINT_GRAPHICS;
    subpass.colorAttachmentCount = 1;
    subpass.pColorAttachments = &colorRef;
    subpass.pResolveAttachments = &resolveRef;

    VkSubpassDependency deps[2]{};
    deps[0].srcSubpass = VK_SUBPASS_EXTERNAL;
    deps[0].dstSubpass = 0;
    deps[0].srcStageMask = VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT;
    deps[0].dstStageMask = VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT;
    deps[0].dstAccessMask = VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT;

    // Ensure resolve is visible to TRANSFER ops that follow (readFrame blit).
    deps[1].srcSubpass = 0;
    deps[1].dstSubpass = VK_SUBPASS_EXTERNAL;
    deps[1].srcStageMask = VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT;
    deps[1].srcAccessMask = VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT;
    deps[1].dstStageMask = VK_PIPELINE_STAGE_TRANSFER_BIT;
    deps[1].dstAccessMask = VK_ACCESS_TRANSFER_READ_BIT;

    VkAttachmentDescription attachments[2] = {msaaAttachment, resolveAttachment};

    VkRenderPassCreateInfo ci{};
    ci.sType = VK_STRUCTURE_TYPE_RENDER_PASS_CREATE_INFO;
    ci.attachmentCount = 2;
    ci.pAttachments = attachments;
    ci.subpassCount = 1;
    ci.pSubpasses = &subpass;
    ci.dependencyCount = 2;
    ci.pDependencies = deps;

    return vkCreateRenderPass(m_device, &ci, nullptr, &m_renderPass) == VK_SUCCESS;
}

// ============================================================================
// Step 7: createUniformBuffer
//   HOST_VISIBLE | HOST_COHERENT so the CPU can write directly each frame.
// ============================================================================

bool VC::VulkanWidget::createUniformBuffer()
{
    VkBufferCreateInfo bi{};
    bi.sType = VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO;
    bi.size = sizeof(UniformData);
    bi.usage = VK_BUFFER_USAGE_UNIFORM_BUFFER_BIT;
    bi.sharingMode = VK_SHARING_MODE_EXCLUSIVE;

    if (vkCreateBuffer(m_device, &bi, nullptr, &m_uniformBuffer) != VK_SUCCESS) {
        return false;
    }

    VkMemoryRequirements memReq;
    vkGetBufferMemoryRequirements(m_device, m_uniformBuffer, &memReq);

    VkMemoryAllocateInfo ai{};
    ai.sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
    ai.allocationSize = memReq.size;
    ai.memoryTypeIndex = findMemoryType(
        memReq.memoryTypeBits,
        VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT
    );

    if (vkAllocateMemory(m_device, &ai, nullptr, &m_uniformMemory) != VK_SUCCESS) {
        return false;
    }

    vkBindBufferMemory(m_device, m_uniformBuffer, m_uniformMemory, 0);
    return true;
}

// ============================================================================
// Step 8: createDescriptorSet
//   Layout + pool + set binding the UBO at binding 0 to the fragment shader.
// ============================================================================

bool VC::VulkanWidget::createDescriptorSet()
{
    // ── set = 0: UBO ──────────────────────────────────────────────────────────
    VkDescriptorSetLayoutBinding uboBinding{};
    uboBinding.binding = 0;
    uboBinding.descriptorType = VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER;
    uboBinding.descriptorCount = 1;
    uboBinding.stageFlags = VK_SHADER_STAGE_FRAGMENT_BIT;

    VkDescriptorSetLayoutCreateInfo uboLci{};
    uboLci.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO;
    uboLci.bindingCount = 1;
    uboLci.pBindings = &uboBinding;
    vkCreateDescriptorSetLayout(m_device, &uboLci, nullptr, &m_descriptorSetLayout);

    VkDescriptorPoolSize uboPs{};
    uboPs.type = VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER;
    uboPs.descriptorCount = 1;

    VkDescriptorPoolCreateInfo uboPci{};
    uboPci.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO;
    uboPci.poolSizeCount = 1;
    uboPci.pPoolSizes = &uboPs;
    uboPci.maxSets = 1;
    vkCreateDescriptorPool(m_device, &uboPci, nullptr, &m_descriptorPool);

    VkDescriptorSetAllocateInfo uboAi{};
    uboAi.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO;
    uboAi.descriptorPool = m_descriptorPool;
    uboAi.descriptorSetCount = 1;
    uboAi.pSetLayouts = &m_descriptorSetLayout;
    vkAllocateDescriptorSets(m_device, &uboAi, &m_descriptorSet);

    VkDescriptorBufferInfo bufInfo{};
    bufInfo.buffer = m_uniformBuffer;
    bufInfo.offset = 0;
    bufInfo.range = sizeof(UniformData);

    VkWriteDescriptorSet uboWrite{};
    uboWrite.sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
    uboWrite.dstSet = m_descriptorSet;
    uboWrite.dstBinding = 0;
    uboWrite.descriptorCount = 1;
    uboWrite.descriptorType = VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER;
    uboWrite.pBufferInfo = &bufInfo;
    vkUpdateDescriptorSets(m_device, 1, &uboWrite, 0, nullptr);

    // ── set = 1: per-mesh combined image sampler ──────────────────────────────
    VkDescriptorSetLayoutBinding texBinding{};
    texBinding.binding = 0;
    texBinding.descriptorType = VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER;
    texBinding.descriptorCount = 1;
    texBinding.stageFlags = VK_SHADER_STAGE_FRAGMENT_BIT;

    VkDescriptorSetLayoutCreateInfo texLci{};
    texLci.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO;
    texLci.bindingCount = 1;
    texLci.pBindings = &texBinding;
    vkCreateDescriptorSetLayout(m_device, &texLci, nullptr, &m_textureSetLayout);

    // Pool supports up to 64 image inputs; FREE_SET_BIT allows individual cleanup.
    VkDescriptorPoolSize texPs{};
    texPs.type = VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER;
    texPs.descriptorCount = 64;

    VkDescriptorPoolCreateInfo texPci{};
    texPci.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO;
    texPci.flags = VK_DESCRIPTOR_POOL_CREATE_FREE_DESCRIPTOR_SET_BIT;
    texPci.poolSizeCount = 1;
    texPci.pPoolSizes = &texPs;
    texPci.maxSets = 64;
    vkCreateDescriptorPool(m_device, &texPci, nullptr, &m_texturePool);

    return true;
}

// ============================================================================
// createShaderModule (helper)
//   Wraps a SPIR-V binary in a VkShaderModule.
//   Can be destroyed once the pipeline is built.
// ============================================================================

VkShaderModule VC::VulkanWidget::createShaderModule(const std::vector<uint32_t>& code)
{
    VkShaderModuleCreateInfo ci{};
    ci.sType = VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO;
    ci.codeSize = code.size() * sizeof(uint32_t);
    ci.pCode = code.data();
    VkShaderModule mod = VK_NULL_HANDLE;
    vkCreateShaderModule(m_device, &ci, nullptr, &mod);
    return mod;
}

// ============================================================================
// Step 9: createPipeline
//   Vertex layout: pos[2] + uv[2] + color[4] + extra[4] floats → stride = 48 bytes.
//   Vertex binding uses the project Vertex struct:
//     pos[2] + uv[2] + color[4] floats → stride = 32 bytes.
//   Only pos (location 0) and uv (location 1) are declared as shader inputs;
//   color is present in the buffer but unused by the current shaders.
// ============================================================================

bool VC::VulkanWidget::createPipeline()
{
    auto vertSpv = compileGLSL(loadShaderSource("vert.glsl"), VK_SHADER_STAGE_VERTEX_BIT);
    auto fragSpv = compileGLSL(loadShaderSource("frag.glsl"), VK_SHADER_STAGE_FRAGMENT_BIT);
    if (vertSpv.empty() || fragSpv.empty()) {
        return false;
    }

    VkShaderModule vert = createShaderModule(vertSpv);
    VkShaderModule frag = createShaderModule(fragSpv);

    VkPipelineShaderStageCreateInfo stages[2]{};
    stages[0].sType = VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO;
    stages[0].stage = VK_SHADER_STAGE_VERTEX_BIT;
    stages[0].module = vert;
    stages[0].pName = "main";
    stages[1].sType = VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO;
    stages[1].stage = VK_SHADER_STAGE_FRAGMENT_BIT;
    stages[1].module = frag;
    stages[1].pName = "main";

    // stride = sizeof(Vertex) = 48 bytes (pos[2] + uv[2] + color[4] + extra[4] × 4 bytes each).
    VkVertexInputBindingDescription binding{};
    binding.binding = 0;
    binding.stride = sizeof(Vertex);
    binding.inputRate = VK_VERTEX_INPUT_RATE_VERTEX;

    VkVertexInputAttributeDescription attrs[4]{};
    attrs[0].binding = 0;
    attrs[0].location = 0; // layout(location=0) in vec2 inPos
    attrs[0].format = VK_FORMAT_R32G32_SFLOAT;
    attrs[0].offset = offsetof(Vertex, pos);
    attrs[1].binding = 0;
    attrs[1].location = 1; // layout(location=1) in vec2 inUV
    attrs[1].format = VK_FORMAT_R32G32_SFLOAT;
    attrs[1].offset = offsetof(Vertex, uv);
    attrs[2].binding = 0;
    attrs[2].location = 2; // layout(location=2) in vec4 inColor
    attrs[2].format = VK_FORMAT_R32G32B32A32_SFLOAT;
    attrs[2].offset = offsetof(Vertex, color);
    attrs[3].binding = 0;
    attrs[3].location = 3; // layout(location=3) in vec4 inExtra  ([0] = draw mode)
    attrs[3].format = VK_FORMAT_R32G32B32A32_SFLOAT;
    attrs[3].offset = offsetof(Vertex, extra);
    VkPipelineVertexInputStateCreateInfo vi{};
    vi.sType = VK_STRUCTURE_TYPE_PIPELINE_VERTEX_INPUT_STATE_CREATE_INFO;
    vi.vertexBindingDescriptionCount = 1;
    vi.pVertexBindingDescriptions = &binding;
    vi.vertexAttributeDescriptionCount = 4;
    vi.pVertexAttributeDescriptions = attrs;

    VkPipelineInputAssemblyStateCreateInfo ia{};
    ia.sType = VK_STRUCTURE_TYPE_PIPELINE_INPUT_ASSEMBLY_STATE_CREATE_INFO;
    ia.topology = VK_PRIMITIVE_TOPOLOGY_TRIANGLE_LIST;

    VkDynamicState                   dynStates[] = {VK_DYNAMIC_STATE_VIEWPORT, VK_DYNAMIC_STATE_SCISSOR};
    VkPipelineDynamicStateCreateInfo dyn{};
    dyn.sType = VK_STRUCTURE_TYPE_PIPELINE_DYNAMIC_STATE_CREATE_INFO;
    dyn.dynamicStateCount = 2;
    dyn.pDynamicStates = dynStates;

    VkPipelineViewportStateCreateInfo vs{};
    vs.sType = VK_STRUCTURE_TYPE_PIPELINE_VIEWPORT_STATE_CREATE_INFO;
    vs.viewportCount = 1;
    vs.scissorCount = 1;

    VkPipelineRasterizationStateCreateInfo rs{};
    rs.sType = VK_STRUCTURE_TYPE_PIPELINE_RASTERIZATION_STATE_CREATE_INFO;
    rs.polygonMode = VK_POLYGON_MODE_FILL;
    rs.cullMode = VK_CULL_MODE_NONE;
    rs.frontFace = VK_FRONT_FACE_CLOCKWISE;
    rs.lineWidth = 1.0f;

    VkPipelineMultisampleStateCreateInfo ms{};
    ms.sType = VK_STRUCTURE_TYPE_PIPELINE_MULTISAMPLE_STATE_CREATE_INFO;
    ms.rasterizationSamples = VK_SAMPLE_COUNT_4_BIT;

    // One color-blend attachment (and one full create-info) per blend mode —
    // only pColorBlendState varies between the variants. See BlendModes.hpp.
    VkPipelineColorBlendAttachmentState blendAttach[kBlendModeCount];
    VkPipelineColorBlendStateCreateInfo blendState[kBlendModeCount]{};
    for (int m = 0; m < kBlendModeCount; ++m) {
        blendAttach[m] = blendAttachmentFor(m);
        blendState[m].sType = VK_STRUCTURE_TYPE_PIPELINE_COLOR_BLEND_STATE_CREATE_INFO;
        blendState[m].attachmentCount = 1;
        blendState[m].pAttachments = &blendAttach[m];
    }

    VkDescriptorSetLayout setLayouts[] = {m_descriptorSetLayout, m_textureSetLayout};

    VkPipelineLayoutCreateInfo layoutCI{};
    layoutCI.sType = VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO;
    layoutCI.setLayoutCount = 2;
    layoutCI.pSetLayouts = setLayouts;
    vkCreatePipelineLayout(m_device, &layoutCI, nullptr, &m_pipelineLayout);

    VkGraphicsPipelineCreateInfo cis[kBlendModeCount]{};
    for (int m = 0; m < kBlendModeCount; ++m) {
        cis[m].sType = VK_STRUCTURE_TYPE_GRAPHICS_PIPELINE_CREATE_INFO;
        cis[m].stageCount = 2;
        cis[m].pStages = stages;
        cis[m].pVertexInputState = &vi;
        cis[m].pInputAssemblyState = &ia;
        cis[m].pViewportState = &vs;
        cis[m].pRasterizationState = &rs;
        cis[m].pMultisampleState = &ms;
        cis[m].pColorBlendState = &blendState[m];
        cis[m].pDynamicState = &dyn;
        cis[m].layout = m_pipelineLayout;
        cis[m].renderPass = m_renderPass;
    }

    bool ok = vkCreateGraphicsPipelines(
                  m_device, VK_NULL_HANDLE, kBlendModeCount, cis, nullptr, m_pipelines
              ) == VK_SUCCESS;

    // Shader modules are only needed during pipeline creation.
    vkDestroyShaderModule(m_device, vert, nullptr);
    vkDestroyShaderModule(m_device, frag, nullptr);
    return ok;
}

// ============================================================================
// findMemoryType (helper)
//   Returns the index of the first memory type that satisfies both the buffer's
//   requirements (filter bitmask) and the desired property flags.
// ============================================================================

uint32_t VC::VulkanWidget::findMemoryType(uint32_t filter, VkMemoryPropertyFlags props)
{
    VkPhysicalDeviceMemoryProperties memProps;
    vkGetPhysicalDeviceMemoryProperties(m_physicalDevice, &memProps);

    for (uint32_t i = 0; i < memProps.memoryTypeCount; i++) {
        if ((filter & (1 << i)) &&
            (memProps.memoryTypes[i].propertyFlags & props) == props) {
            return i;
        }
    }
    return 0;
}

// ============================================================================
// Step 10: createVertexBuffer / createIndexBuffer
//   Fixed-capacity HOST_VISIBLE | HOST_COHERENT buffers.  Actual geometry is
//   uploaded each frame via setMeshes() → recordCommandBuffer().
//   65536 vertices × 32 bytes = 2 MB; 65536 indices × 2 bytes = 128 KB.
// ============================================================================

static constexpr VkDeviceSize MAX_VERTEX_BUFFER_SIZE = sizeof(Vertex) * 262144;
static constexpr VkDeviceSize MAX_INDEX_BUFFER_SIZE = sizeof(uint32_t) * 262144;

static bool createBuffer(
    VkDevice                                                 device,
    VkDeviceSize                                             size,
    VkBufferUsageFlags                                       usage,
    VkBuffer&                                                outBuffer,
    VkDeviceMemory&                                          outMemory,
    std::function<uint32_t(uint32_t, VkMemoryPropertyFlags)> findMemType
)
{
    VkBufferCreateInfo bi{};
    bi.sType = VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO;
    bi.size = size;
    bi.usage = usage;
    bi.sharingMode = VK_SHARING_MODE_EXCLUSIVE;

    if (vkCreateBuffer(device, &bi, nullptr, &outBuffer) != VK_SUCCESS) {
        return false;
    }

    VkMemoryRequirements memReq;
    vkGetBufferMemoryRequirements(device, outBuffer, &memReq);

    VkMemoryAllocateInfo ai{};
    ai.sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
    ai.allocationSize = memReq.size;
    ai.memoryTypeIndex = findMemType(
        memReq.memoryTypeBits,
        VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT
    );

    if (vkAllocateMemory(device, &ai, nullptr, &outMemory) != VK_SUCCESS) {
        return false;
    }

    vkBindBufferMemory(device, outBuffer, outMemory, 0);
    return true;
}

bool VC::VulkanWidget::createVertexBuffer()
{
    return createBuffer(m_device, MAX_VERTEX_BUFFER_SIZE, VK_BUFFER_USAGE_VERTEX_BUFFER_BIT, m_vertexBuffer, m_vertexMemory, [this](uint32_t f, VkMemoryPropertyFlags p) {
        return findMemoryType(f, p);
    });
}

bool VC::VulkanWidget::createIndexBuffer()
{
    return createBuffer(m_device, MAX_INDEX_BUFFER_SIZE, VK_BUFFER_USAGE_INDEX_BUFFER_BIT, m_indexBuffer, m_indexMemory, [this](uint32_t f, VkMemoryPropertyFlags p) {
        return findMemoryType(f, p);
    });
}

// ============================================================================
// Step 11: createFramebuffers
//   One framebuffer per swapchain image (MSAA → swapchain resolve) for live
//   rendering, plus one extra framebuffer that resolves into m_resolveImage
//   for offscreen readFrame().
// ============================================================================

bool VC::VulkanWidget::createFramebuffers()
{
    const size_t swapCount = m_swapImages.size();
    m_framebuffers.resize(swapCount + 1);

    VkFramebufferCreateInfo ci{};
    ci.sType = VK_STRUCTURE_TYPE_FRAMEBUFFER_CREATE_INFO;
    ci.renderPass = m_renderPass;
    ci.attachmentCount = 2;
    ci.width = m_swapExtent.width;
    ci.height = m_swapExtent.height;
    ci.layers = 1;

    // Per-swapchain-image framebuffers: resolve directly into swapchain image.
    for (size_t i = 0; i < swapCount; ++i) {
        VkImageView attachments[2] = {m_ssaaImageView, m_swapImageViews[i]};
        ci.pAttachments = attachments;
        VkResult r = vkCreateFramebuffer(m_device, &ci, nullptr, &m_framebuffers[i]);
        if (r != VK_SUCCESS) {
            qWarning("createFramebuffers[%zu] failed: %d", i, r);
            return false;
        }
    }

    // Extra readFrame framebuffer: resolve into m_resolveImage.
    VkImageView readAttachments[2] = {m_ssaaImageView, m_resolveImageView};
    ci.pAttachments = readAttachments;
    return vkCreateFramebuffer(m_device, &ci, nullptr, &m_framebuffers[swapCount]) == VK_SUCCESS;
}

// ============================================================================
// Step 12: createCommandPool
//   RESET_COMMAND_BUFFER_BIT lets us reset and re-record individual buffers.
// ============================================================================

bool VC::VulkanWidget::createCommandPool()
{
    VkCommandPoolCreateInfo ci{};
    ci.sType = VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO;
    ci.flags = VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT;
    ci.queueFamilyIndex = m_graphicsFamily;
    return vkCreateCommandPool(m_device, &ci, nullptr, &m_commandPool) == VK_SUCCESS;
}

// ============================================================================
// Step 12b: createCommandBuffers
//   Single reusable primary command buffer; reset and re-recorded every frame.
// ============================================================================

bool VC::VulkanWidget::createCommandBuffers()
{
    VkCommandBufferAllocateInfo ai{};
    ai.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO;
    ai.commandPool = m_commandPool;
    ai.level = VK_COMMAND_BUFFER_LEVEL_PRIMARY;
    ai.commandBufferCount = 1;
    return vkAllocateCommandBuffers(m_device, &ai, &m_commandBuffer) == VK_SUCCESS;
}

// ============================================================================
// Step 13: createSyncObjects
//   Two semaphores (GPU↔GPU) and one fence (CPU↔GPU, pre-signalled for frame 0).
// ============================================================================

bool VC::VulkanWidget::createSyncObjects()
{
    VkSemaphoreCreateInfo si{};
    si.sType = VK_STRUCTURE_TYPE_SEMAPHORE_CREATE_INFO;

    VkFenceCreateInfo fi{};
    fi.sType = VK_STRUCTURE_TYPE_FENCE_CREATE_INFO;
    fi.flags = VK_FENCE_CREATE_SIGNALED_BIT; // Pre-signalled so frame 0 doesn't block.

    return vkCreateSemaphore(m_device, &si, nullptr, &m_imageAvailableSemaphore) == VK_SUCCESS && vkCreateSemaphore(m_device, &si, nullptr, &m_renderFinishedSemaphore) == VK_SUCCESS && vkCreateFence(m_device, &fi, nullptr, &m_inFlightFence) == VK_SUCCESS;
}

// ============================================================================
// updateUniforms — called once per frame
//   Maps the uniform buffer and writes elapsed time + current resolution.
//   HOST_COHERENT memory means no explicit flush needed.
// ============================================================================

void VC::VulkanWidget::updateUniforms()
{
    static auto start = std::chrono::high_resolution_clock::now();
    auto        now = std::chrono::high_resolution_clock::now();
    float       t = std::chrono::duration<float>(now - start).count();

    UniformData ubo{};
    ubo.time = t;
    ubo.resolution[0] = (float)m_swapExtent.width;
    ubo.resolution[1] = (float)m_swapExtent.height;
    ubo.pixelSize = 1.f / std::min((float)m_swapExtent.width, (float)m_swapExtent.height);

    void* data;
    vkMapMemory(m_device, m_uniformMemory, 0, sizeof(UniformData), 0, &data);
    memcpy(data, &ubo, sizeof(UniformData));
    vkUnmapMemory(m_device, m_uniformMemory);
}

// ============================================================================
// Texture upload helpers
// ============================================================================

// Run a single one-shot command buffer synchronously on the graphics queue.
static void runOneShot(VkDevice device, VkCommandPool pool, VkQueue queue, const std::function<void(VkCommandBuffer)>& fn)
{
    VkCommandBufferAllocateInfo ai{};
    ai.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO;
    ai.commandPool = pool;
    ai.level = VK_COMMAND_BUFFER_LEVEL_PRIMARY;
    ai.commandBufferCount = 1;

    VkCommandBuffer cb = VK_NULL_HANDLE;
    vkAllocateCommandBuffers(device, &ai, &cb);

    VkCommandBufferBeginInfo bi{};
    bi.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO;
    bi.flags = VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT;
    vkBeginCommandBuffer(cb, &bi);

    fn(cb);

    vkEndCommandBuffer(cb);

    VkSubmitInfo si{};
    si.sType = VK_STRUCTURE_TYPE_SUBMIT_INFO;
    si.commandBufferCount = 1;
    si.pCommandBuffers = &cb;
    vkQueueSubmit(queue, 1, &si, VK_NULL_HANDLE);
    vkQueueWaitIdle(queue);

    vkFreeCommandBuffers(device, pool, 1, &cb);
}

void VC::VulkanWidget::transitionImageLayout(VkImage image, VkImageLayout from, VkImageLayout to)
{
    runOneShot(m_device, m_commandPool, m_graphicsQueue, [&](VkCommandBuffer cb) {
        VkImageMemoryBarrier barrier{};
        barrier.sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER;
        barrier.oldLayout = from;
        barrier.newLayout = to;
        barrier.srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
        barrier.dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
        barrier.image = image;
        barrier.subresourceRange = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1};

        VkPipelineStageFlags srcStage{}, dstStage{};

        if (from == VK_IMAGE_LAYOUT_UNDEFINED && to == VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL) {
            barrier.srcAccessMask = 0;
            barrier.dstAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT;
            srcStage = VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT;
            dstStage = VK_PIPELINE_STAGE_TRANSFER_BIT;
        } else {
            barrier.srcAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT;
            barrier.dstAccessMask = VK_ACCESS_SHADER_READ_BIT;
            srcStage = VK_PIPELINE_STAGE_TRANSFER_BIT;
            dstStage = VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT;
        }

        vkCmdPipelineBarrier(cb, srcStage, dstStage, 0, 0, nullptr, 0, nullptr, 1, &barrier);
    });
}

void VC::VulkanWidget::copyBufferToImage(VkBuffer buf, VkImage image, uint32_t w, uint32_t h)
{
    runOneShot(m_device, m_commandPool, m_graphicsQueue, [&](VkCommandBuffer cb) {
        VkBufferImageCopy region{};
        region.imageSubresource = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 0, 1};
        region.imageExtent = {w, h, 1};
        vkCmdCopyBufferToImage(cb, buf, image, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, 1, &region);
    });
}

VkDescriptorSet VC::VulkanWidget::uploadTexture(const cv::Mat& mat)
{
    uint32_t     w = static_cast<uint32_t>(mat.cols);
    uint32_t     h = static_cast<uint32_t>(mat.rows);
    VkDeviceSize imageSize = static_cast<VkDeviceSize>(w * h * 4);

    // ── Staging buffer ────────────────────────────────────────────────────────
    VkBuffer       stagingBuf = VK_NULL_HANDLE;
    VkDeviceMemory stagingMem = VK_NULL_HANDLE;
    createBuffer(m_device, imageSize, VK_BUFFER_USAGE_TRANSFER_SRC_BIT, stagingBuf, stagingMem, [this](uint32_t f, VkMemoryPropertyFlags p) { return findMemoryType(f, p); });

    void* data;
    vkMapMemory(m_device, stagingMem, 0, imageSize, 0, &data);
    std::memcpy(data, mat.data, static_cast<size_t>(imageSize));
    vkUnmapMemory(m_device, stagingMem);

    // ── VkImage ───────────────────────────────────────────────────────────────
    TextureResource tex{};

    VkImageCreateInfo ici{};
    ici.sType = VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO;
    ici.imageType = VK_IMAGE_TYPE_2D;
    ici.format = VK_FORMAT_B8G8R8A8_UNORM; // matches OpenCV BGRA layout
    ici.extent = {w, h, 1};
    ici.mipLevels = 1;
    ici.arrayLayers = 1;
    ici.samples = VK_SAMPLE_COUNT_1_BIT;
    ici.tiling = VK_IMAGE_TILING_OPTIMAL;
    ici.usage = VK_IMAGE_USAGE_TRANSFER_DST_BIT | VK_IMAGE_USAGE_SAMPLED_BIT;
    ici.sharingMode = VK_SHARING_MODE_EXCLUSIVE;
    ici.initialLayout = VK_IMAGE_LAYOUT_UNDEFINED;
    vkCreateImage(m_device, &ici, nullptr, &tex.image);

    VkMemoryRequirements memReq;
    vkGetImageMemoryRequirements(m_device, tex.image, &memReq);

    VkMemoryAllocateInfo mai{};
    mai.sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
    mai.allocationSize = memReq.size;
    mai.memoryTypeIndex = findMemoryType(memReq.memoryTypeBits, VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT);
    vkAllocateMemory(m_device, &mai, nullptr, &tex.memory);
    vkBindImageMemory(m_device, tex.image, tex.memory, 0);

    // ── Upload ────────────────────────────────────────────────────────────────
    transitionImageLayout(tex.image, VK_IMAGE_LAYOUT_UNDEFINED, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL);
    copyBufferToImage(stagingBuf, tex.image, w, h);
    transitionImageLayout(tex.image, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL);

    vkDestroyBuffer(m_device, stagingBuf, nullptr);
    vkFreeMemory(m_device, stagingMem, nullptr);

    // ── ImageView + Sampler ───────────────────────────────────────────────────
    VkImageViewCreateInfo ivci{};
    ivci.sType = VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO;
    ivci.image = tex.image;
    ivci.viewType = VK_IMAGE_VIEW_TYPE_2D;
    ivci.format = VK_FORMAT_B8G8R8A8_UNORM;
    ivci.subresourceRange = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1};
    vkCreateImageView(m_device, &ivci, nullptr, &tex.view);

    VkSamplerCreateInfo sci{};
    sci.sType = VK_STRUCTURE_TYPE_SAMPLER_CREATE_INFO;
    sci.magFilter = VK_FILTER_LINEAR;
    sci.minFilter = VK_FILTER_LINEAR;
    sci.addressModeU = VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE;
    sci.addressModeV = VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE;
    sci.addressModeW = VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE;
    sci.maxLod = 0.f;
    vkCreateSampler(m_device, &sci, nullptr, &tex.sampler);

    // ── Descriptor set ────────────────────────────────────────────────────────
    VkDescriptorSetAllocateInfo dsAi{};
    dsAi.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO;
    dsAi.descriptorPool = m_texturePool;
    dsAi.descriptorSetCount = 1;
    dsAi.pSetLayouts = &m_textureSetLayout;

    VkDescriptorSet descSet = VK_NULL_HANDLE;
    vkAllocateDescriptorSets(m_device, &dsAi, &descSet);

    VkDescriptorImageInfo imgInfo{};
    imgInfo.imageLayout = VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL;
    imgInfo.imageView = tex.view;
    imgInfo.sampler = tex.sampler;

    VkWriteDescriptorSet dsWrite{};
    dsWrite.sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
    dsWrite.dstSet = descSet;
    dsWrite.dstBinding = 0;
    dsWrite.descriptorCount = 1;
    dsWrite.descriptorType = VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER;
    dsWrite.pImageInfo = &imgInfo;
    vkUpdateDescriptorSets(m_device, 1, &dsWrite, 0, nullptr);

    m_textureIndex[descSet] = m_textures.size();
    m_textures.push_back(tex);
    return descSet;
}

void VC::VulkanWidget::updateTexturePixels(VkDescriptorSet desc, const cv::Mat& mat)
{
    auto it = m_textureIndex.find(desc);
    if (it == m_textureIndex.end()) return;
    TextureResource& tex = m_textures[it->second];

    uint32_t     w = static_cast<uint32_t>(mat.cols);
    uint32_t     h = static_cast<uint32_t>(mat.rows);
    VkDeviceSize imageSize = static_cast<VkDeviceSize>(w * h * 4);

    VkBuffer       stagingBuf = VK_NULL_HANDLE;
    VkDeviceMemory stagingMem = VK_NULL_HANDLE;
    createBuffer(m_device, imageSize, VK_BUFFER_USAGE_TRANSFER_SRC_BIT, stagingBuf, stagingMem, [this](uint32_t f, VkMemoryPropertyFlags p) { return findMemoryType(f, p); });

    void* data;
    vkMapMemory(m_device, stagingMem, 0, imageSize, 0, &data);
    std::memcpy(data, mat.data, static_cast<size_t>(imageSize));
    vkUnmapMemory(m_device, stagingMem);

    transitionImageLayout(tex.image, VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL);
    copyBufferToImage(stagingBuf, tex.image, w, h);
    transitionImageLayout(tex.image, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL);

    vkDestroyBuffer(m_device, stagingBuf, nullptr);
    vkFreeMemory(m_device, stagingMem, nullptr);
}

// ============================================================================
// recordCommandBuffer — called every frame
//   Resets and re-records: uniform upload → optional vertex re-upload →
//   beginRenderPass → bindPipeline → bindDescriptors → draw → endRenderPass.
// ============================================================================

void VC::VulkanWidget::recordCommandBuffer(VkCommandBuffer cb, uint32_t imageIndex)
{
    updateUniforms();

    if (m_geomDirty) {
        if (!m_vertices.empty()) {
            VkDeviceSize vSize = sizeof(Vertex) * m_vertices.size();
            void*        data;
            vkMapMemory(m_device, m_vertexMemory, 0, vSize, 0, &data);
            memcpy(data, m_vertices.data(), vSize);
            vkUnmapMemory(m_device, m_vertexMemory);
        }
        if (!m_indices.empty()) {
            VkDeviceSize iSize = sizeof(uint32_t) * m_indices.size();
            void*        data;
            vkMapMemory(m_device, m_indexMemory, 0, iSize, 0, &data);
            memcpy(data, m_indices.data(), iSize);
            vkUnmapMemory(m_device, m_indexMemory);
        }
        m_geomDirty = false;
    }

    VkCommandBufferBeginInfo bi{};
    bi.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO;
    vkBeginCommandBuffer(cb, &bi);

    // ── Effect pre-passes (per-mesh, into m_effectResults) ────────────────
    recordEffectPrepasses(cb);

    VkClearValue clearValues[2]{};
    clearValues[0] = {{{m_bgColor[0], m_bgColor[1], m_bgColor[2], 1.0f}}}; // MSAA attachment clear # Color (scene BG)
    // clearValues[1] unused (resolve attachment has loadOp=DONT_CARE)

    VkViewport vp{0, 0, (float)m_swapExtent.width, (float)m_swapExtent.height, 0, 1};
    VkRect2D   sc{{0, 0}, m_swapExtent};

    VkRenderPassBeginInfo rpi{};
    rpi.sType = VK_STRUCTURE_TYPE_RENDER_PASS_BEGIN_INFO;
    rpi.renderPass = m_renderPass;
    rpi.framebuffer = m_framebuffers[imageIndex];
    rpi.renderArea.extent = m_swapExtent;
    rpi.clearValueCount = 2;
    rpi.pClearValues = clearValues;

    vkCmdBeginRenderPass(cb, &rpi, VK_SUBPASS_CONTENTS_INLINE);
    vkCmdSetViewport(cb, 0, 1, &vp);
    vkCmdSetScissor(cb, 0, 1, &sc);
    // Normal pipeline as a baseline; recordSceneDraws rebinds per mesh by blend
    // mode. set=0 persists across those rebinds (shared m_pipelineLayout).
    vkCmdBindPipeline(cb, VK_PIPELINE_BIND_POINT_GRAPHICS, m_pipelines[0]);
    vkCmdBindDescriptorSets(cb, VK_PIPELINE_BIND_POINT_GRAPHICS, m_pipelineLayout, 0, 1, &m_descriptorSet, 0, nullptr);

    recordSceneDraws(cb);

    vkCmdEndRenderPass(cb);
    // Render pass resolved MSAA → swapchain image, leaving it in TRANSFER_SRC_OPTIMAL.
    // Transition it to PRESENT_SRC_KHR so the compositor can display it.

    VkImageMemoryBarrier toPresent{};
    toPresent.sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER;
    toPresent.srcAccessMask = VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT;
    toPresent.dstAccessMask = 0;
    toPresent.oldLayout = VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL;
    toPresent.newLayout = VK_IMAGE_LAYOUT_PRESENT_SRC_KHR;
    toPresent.srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
    toPresent.dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
    toPresent.image = m_swapImages[imageIndex];
    toPresent.subresourceRange = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1};
    vkCmdPipelineBarrier(cb, VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT, VK_PIPELINE_STAGE_BOTTOM_OF_PIPE_BIT, 0, 0, nullptr, 0, nullptr, 1, &toPresent);

    vkEndCommandBuffer(cb);
}

// ============================================================================
// readFrame — offscreen render + CPU readback
//   Renders the current scene to the SSAA image, blits it down to the
//   readback image (linear, host-visible), then maps the memory and copies
//   the pixels into a cv::Mat. Used by Compiler::generateVideo().
//   Blocks until the GPU is done (vkQueueWaitIdle).
// ============================================================================

cv::Mat VC::VulkanWidget::readFrame()
{
    // Upload geometry if dirty.
    updateUniforms();
    if (m_geomDirty) {
        if (!m_vertices.empty()) {
            VkDeviceSize sz = sizeof(Vertex) * m_vertices.size();
            void*        data;
            vkMapMemory(m_device, m_vertexMemory, 0, sz, 0, &data);
            memcpy(data, m_vertices.data(), sz);
            vkUnmapMemory(m_device, m_vertexMemory);
        }
        if (!m_indices.empty()) {
            VkDeviceSize sz = sizeof(uint32_t) * m_indices.size();
            void*        data;
            vkMapMemory(m_device, m_indexMemory, 0, sz, 0, &data);
            memcpy(data, m_indices.data(), sz);
            vkUnmapMemory(m_device, m_indexMemory);
        }
        m_geomDirty = false;
    }

    vkResetCommandBuffer(m_commandBuffer, 0);

    VkCommandBufferBeginInfo bi{};
    bi.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO;
    vkBeginCommandBuffer(m_commandBuffer, &bi);

    // ── Render pass → MSAA resolve image ─────────────────────────────────
    VkClearValue clearValues[2]{};
    clearValues[0] = {{{m_bgColor[0], m_bgColor[1], m_bgColor[2], 1.0f}}}; // # Color (scene BG)
    VkViewport vp{0, 0, (float)m_swapExtent.width, (float)m_swapExtent.height, 0, 1};
    VkRect2D   sc{{0, 0}, m_swapExtent};

    VkRenderPassBeginInfo rpi{};
    rpi.sType = VK_STRUCTURE_TYPE_RENDER_PASS_BEGIN_INFO;
    rpi.renderPass = m_renderPass;
    rpi.framebuffer = m_framebuffers.back();
    rpi.renderArea.extent = m_swapExtent;
    rpi.clearValueCount = 2;
    rpi.pClearValues = clearValues;

    // ── Effect pre-passes (per-mesh, into m_effectResults) ────────────────
    recordEffectPrepasses(m_commandBuffer);

    vkCmdBeginRenderPass(m_commandBuffer, &rpi, VK_SUBPASS_CONTENTS_INLINE);
    vkCmdSetViewport(m_commandBuffer, 0, 1, &vp);
    vkCmdSetScissor(m_commandBuffer, 0, 1, &sc);
    vkCmdBindPipeline(m_commandBuffer, VK_PIPELINE_BIND_POINT_GRAPHICS, m_pipelines[0]);
    vkCmdBindDescriptorSets(m_commandBuffer, VK_PIPELINE_BIND_POINT_GRAPHICS, m_pipelineLayout, 0, 1, &m_descriptorSet, 0, nullptr);

    recordSceneDraws(m_commandBuffer);

    vkCmdEndRenderPass(m_commandBuffer);
    // m_resolveImage is now in TRANSFER_SRC_OPTIMAL (render pass finalLayout).

    // ── Transition readback image UNDEFINED → TRANSFER_DST ───────────────
    VkImageMemoryBarrier toReadDst{};
    toReadDst.sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER;
    toReadDst.srcAccessMask = 0;
    toReadDst.dstAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT;
    toReadDst.oldLayout = VK_IMAGE_LAYOUT_UNDEFINED;
    toReadDst.newLayout = VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL;
    toReadDst.srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
    toReadDst.dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
    toReadDst.image = m_readbackImage;
    toReadDst.subresourceRange = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1};
    vkCmdPipelineBarrier(m_commandBuffer, VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT, 0, 0, nullptr, 0, nullptr, 1, &toReadDst);

    // ── Blit resolve image → readback (same size, copies resolved pixels) ─
    VkImageBlit blit{};
    blit.srcSubresource = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 0, 1};
    blit.srcOffsets[0] = {0, 0, 0};
    blit.srcOffsets[1] = {(int32_t)m_swapExtent.width, (int32_t)m_swapExtent.height, 1};
    blit.dstSubresource = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 0, 1};
    blit.dstOffsets[0] = {0, 0, 0};
    blit.dstOffsets[1] = {(int32_t)m_swapExtent.width, (int32_t)m_swapExtent.height, 1};
    vkCmdBlitImage(m_commandBuffer, m_resolveImage, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL, m_readbackImage, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, 1, &blit, VK_FILTER_LINEAR);

    // ── Transition readback TRANSFER_DST → GENERAL (host read) ───────────
    VkImageMemoryBarrier toGeneral{};
    toGeneral.sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER;
    toGeneral.srcAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT;
    toGeneral.dstAccessMask = VK_ACCESS_HOST_READ_BIT;
    toGeneral.oldLayout = VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL;
    toGeneral.newLayout = VK_IMAGE_LAYOUT_GENERAL;
    toGeneral.srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
    toGeneral.dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
    toGeneral.image = m_readbackImage;
    toGeneral.subresourceRange = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1};
    vkCmdPipelineBarrier(m_commandBuffer, VK_PIPELINE_STAGE_TRANSFER_BIT, VK_PIPELINE_STAGE_HOST_BIT, 0, 0, nullptr, 0, nullptr, 1, &toGeneral);

    vkEndCommandBuffer(m_commandBuffer);

    // ── Submit and wait ───────────────────────────────────────────────────
    VkSubmitInfo si{};
    si.sType = VK_STRUCTURE_TYPE_SUBMIT_INFO;
    si.commandBufferCount = 1;
    si.pCommandBuffers = &m_commandBuffer;
    vkQueueSubmit(m_graphicsQueue, 1, &si, VK_NULL_HANDLE);
    vkQueueWaitIdle(m_graphicsQueue);

    // ── Map and copy to cv::Mat ───────────────────────────────────────────
    VkImageSubresource  subRes{VK_IMAGE_ASPECT_COLOR_BIT, 0, 0};
    VkSubresourceLayout layout{};
    vkGetImageSubresourceLayout(m_device, m_readbackImage, &subRes, &layout);

    void* data;
    vkMapMemory(m_device, m_readbackMemory, 0, VK_WHOLE_SIZE, 0, &data);

    uint32_t W = m_swapExtent.width;
    uint32_t H = m_swapExtent.height;
    cv::Mat  result(H, W, CV_8UC4);
    uint8_t* src = static_cast<uint8_t*>(data) + layout.offset;
    for (uint32_t row = 0; row < H; ++row) {
        memcpy(result.ptr(row), src + row * layout.rowPitch, W * 4);
    }

    vkUnmapMemory(m_device, m_readbackMemory);
    return result;
}

// ============================================================================
// render — main per-frame driver
//   wait → acquire → record → submit → present → request next repaint.
// ============================================================================

void VC::VulkanWidget::render()
{
    if (!m_initialized) {
        return;
    }

    using Clock = std::chrono::high_resolution_clock;
    using Ms = std::chrono::duration<double, std::milli>;

    auto t = [](auto t0) { return std::chrono::duration_cast<Ms>(Clock::now() - t0).count(); };

    // --- frameCallback + setMeshes ---
    auto t0 = Clock::now();
    if (m_frameCallback) {
        setMeshes(m_frameCallback());
    }
    [[maybe_unused]] double ms_meshes = t(t0);

    // --- GPU fence (stall waiting for previous frame to finish) ---
    auto t1 = Clock::now();
    vkWaitForFences(m_device, 1, &m_inFlightFence, VK_TRUE, UINT64_MAX);
    vkResetFences(m_device, 1, &m_inFlightFence);
    [[maybe_unused]] double ms_fence = t(t1);

    uint32_t imageIndex;
    VkResult res = vkAcquireNextImageKHR(m_device, m_swapchain, UINT64_MAX, m_imageAvailableSemaphore, VK_NULL_HANDLE, &imageIndex);
    if (res == VK_ERROR_OUT_OF_DATE_KHR) {
        recreateSwapchain();
        return;
    }

    // --- command buffer recording ---
    auto t2 = Clock::now();
    vkResetCommandBuffer(m_commandBuffer, 0);
    recordCommandBuffer(m_commandBuffer, imageIndex);
    [[maybe_unused]] double ms_record = t(t2);

    // --- submit + present ---
    auto                 t3 = Clock::now();
    VkPipelineStageFlags waitStages[] = {VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT};
    VkSubmitInfo         submitInfo{};
    submitInfo.sType = VK_STRUCTURE_TYPE_SUBMIT_INFO;
    submitInfo.waitSemaphoreCount = 1;
    submitInfo.pWaitSemaphores = &m_imageAvailableSemaphore;
    submitInfo.pWaitDstStageMask = waitStages;
    submitInfo.commandBufferCount = 1;
    submitInfo.pCommandBuffers = &m_commandBuffer;
    submitInfo.signalSemaphoreCount = 1;
    submitInfo.pSignalSemaphores = &m_renderFinishedSemaphore;
    vkQueueSubmit(m_graphicsQueue, 1, &submitInfo, m_inFlightFence);

    VkPresentInfoKHR presentInfo{};
    presentInfo.sType = VK_STRUCTURE_TYPE_PRESENT_INFO_KHR;
    presentInfo.waitSemaphoreCount = 1;
    presentInfo.pWaitSemaphores = &m_renderFinishedSemaphore;
    presentInfo.swapchainCount = 1;
    presentInfo.pSwapchains = &m_swapchain;
    presentInfo.pImageIndices = &imageIndex;
    vkQueuePresentKHR(m_graphicsQueue, &presentInfo);
    [[maybe_unused]] double ms_submit = t(t3);

#ifdef VC_DEBUG_ON
    static auto   s_lastPrint = Clock::now();
    static double s_meshes = 0, s_fence = 0, s_record = 0, s_submit = 0;
    static int    s_frames = 0;
    s_meshes += ms_meshes;
    s_fence += ms_fence;
    s_record += ms_record;
    s_submit += ms_submit;
    ++s_frames;
    if (t(s_lastPrint) >= 1000.0) {
        double n = s_frames;
        std::cout << std::format(
            "[render] meshes+upload:{:.1f}ms  fence:{:.1f}ms  record:{:.1f}ms  submit+present:{:.1f}ms  ({} fps)\n",
            s_meshes / n, s_fence / n, s_record / n, s_submit / n, s_frames
        );
        s_meshes = s_fence = s_record = s_submit = 0;
        s_frames = 0;
        s_lastPrint = Clock::now();
    }
#endif

    // windowHandle()->requestUpdate() ties the next repaint to the platform
    // display sync (CADisplayLink on macOS) rather than posting through Qt's
    // event queue, which eliminates the timer-jitter that update() introduces.
    if (windowHandle()) {
        windowHandle()->requestUpdate();
    } else {
        update();
    }
}

// ============================================================================
// recreateSwapchain
//   Called on resize or VK_ERROR_OUT_OF_DATE_KHR.  Only swapchain-dependent
//   objects are destroyed; pipeline, descriptors and buffers are untouched.
// ============================================================================

void VC::VulkanWidget::recreateSwapchain()
{
    vkDeviceWaitIdle(m_device);

    for (auto fb : m_framebuffers) {
        vkDestroyFramebuffer(m_device, fb, nullptr);
    }
    m_framebuffers.clear();

    destroySsaaResources();
    destroyReadbackResources();

    for (auto iv : m_swapImageViews) {
        vkDestroyImageView(m_device, iv, nullptr);
    }
    vkDestroySwapchainKHR(m_device, m_swapchain, nullptr);

    createSwapchain();
    createSsaaResources();
    createReadbackResources();
    createFramebuffers();
}

// ============================================================================
// Effect post-process infrastructure
// ============================================================================

bool VC::VulkanWidget::createEffectResources()
{
    auto fm = [this](uint32_t f, VkMemoryPropertyFlags p) { return findMemoryType(f, p); };

    // Ping/pong images at swapchain resolution
    auto makeImg = [&](VkImage& img, VkDeviceMemory& mem, VkImageView& view) -> bool {
        VkImageCreateInfo ici{};
        ici.sType = VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO;
        ici.imageType = VK_IMAGE_TYPE_2D;
        ici.format = m_swapFormat;
        ici.extent = {m_swapExtent.width, m_swapExtent.height, 1};
        ici.mipLevels = 1;
        ici.arrayLayers = 1;
        ici.samples = VK_SAMPLE_COUNT_1_BIT;
        ici.tiling = VK_IMAGE_TILING_OPTIMAL;
        ici.usage = VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT | VK_IMAGE_USAGE_SAMPLED_BIT;
        ici.sharingMode = VK_SHARING_MODE_EXCLUSIVE;
        ici.initialLayout = VK_IMAGE_LAYOUT_UNDEFINED;
        if (vkCreateImage(m_device, &ici, nullptr, &img) != VK_SUCCESS) return false;

        VkMemoryRequirements req;
        vkGetImageMemoryRequirements(m_device, img, &req);
        VkMemoryAllocateInfo ai{};
        ai.sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
        ai.allocationSize = req.size;
        ai.memoryTypeIndex = fm(req.memoryTypeBits, VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT);
        if (vkAllocateMemory(m_device, &ai, nullptr, &mem) != VK_SUCCESS) return false;
        vkBindImageMemory(m_device, img, mem, 0);

        VkImageViewCreateInfo ivci{};
        ivci.sType = VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO;
        ivci.image = img;
        ivci.viewType = VK_IMAGE_VIEW_TYPE_2D;
        ivci.format = m_swapFormat;
        ivci.subresourceRange = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1};
        return vkCreateImageView(m_device, &ivci, nullptr, &view) == VK_SUCCESS;
    };
    if (!makeImg(m_pingImage, m_pingMemory, m_pingView)) return false;
    if (!makeImg(m_pongImage, m_pongMemory, m_pongView)) return false;

    // Effect render pass: transparent clear, SHADER_READ_ONLY_OPTIMAL final, 1× sample
    {
        VkAttachmentDescription att{};
        att.format = m_swapFormat;
        att.samples = VK_SAMPLE_COUNT_1_BIT;
        att.loadOp = VK_ATTACHMENT_LOAD_OP_CLEAR;
        att.storeOp = VK_ATTACHMENT_STORE_OP_STORE;
        att.stencilLoadOp = VK_ATTACHMENT_LOAD_OP_DONT_CARE;
        att.stencilStoreOp = VK_ATTACHMENT_STORE_OP_DONT_CARE;
        att.initialLayout = VK_IMAGE_LAYOUT_UNDEFINED;
        att.finalLayout = VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL;

        VkAttachmentReference ref{0, VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL};

        VkSubpassDescription sub{};
        sub.pipelineBindPoint = VK_PIPELINE_BIND_POINT_GRAPHICS;
        sub.colorAttachmentCount = 1;
        sub.pColorAttachments = &ref;

        VkSubpassDependency deps[2]{};
        // RAW: colour-attachment writes visible to subsequent fragment-shader reads
        deps[0].srcSubpass = 0;
        deps[0].dstSubpass = VK_SUBPASS_EXTERNAL;
        deps[0].srcStageMask = VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT;
        deps[0].srcAccessMask = VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT;
        deps[0].dstStageMask = VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT;
        deps[0].dstAccessMask = VK_ACCESS_SHADER_READ_BIT;
        // WAR: preceding fragment-shader reads complete before colour-attachment writes.
        // Without this the V-blur LOAD_OP_CLEAR races with H-blur still sampling ping.
        deps[1].srcSubpass = VK_SUBPASS_EXTERNAL;
        deps[1].dstSubpass = 0;
        deps[1].srcStageMask = VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT;
        deps[1].srcAccessMask = VK_ACCESS_SHADER_READ_BIT;
        deps[1].dstStageMask = VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT;
        deps[1].dstAccessMask = VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT;

        VkRenderPassCreateInfo rpci{};
        rpci.sType = VK_STRUCTURE_TYPE_RENDER_PASS_CREATE_INFO;
        rpci.attachmentCount = 1;
        rpci.pAttachments = &att;
        rpci.subpassCount = 1;
        rpci.pSubpasses = &sub;
        rpci.dependencyCount = 2;
        rpci.pDependencies = deps;
        if (vkCreateRenderPass(m_device, &rpci, nullptr, &m_effectPass) != VK_SUCCESS) return false;
    }

    // Framebuffers
    auto makeFb = [&](VkImageView view, VkFramebuffer& fb) -> bool {
        VkFramebufferCreateInfo fci{};
        fci.sType = VK_STRUCTURE_TYPE_FRAMEBUFFER_CREATE_INFO;
        fci.renderPass = m_effectPass;
        fci.attachmentCount = 1;
        fci.pAttachments = &view;
        fci.width = m_swapExtent.width;
        fci.height = m_swapExtent.height;
        fci.layers = 1;
        return vkCreateFramebuffer(m_device, &fci, nullptr, &fb) == VK_SUCCESS;
    };
    if (!makeFb(m_pingView, m_pingFb)) return false;
    if (!makeFb(m_pongView, m_pongFb)) return false;

    // Sampler
    {
        VkSamplerCreateInfo sci{};
        sci.sType = VK_STRUCTURE_TYPE_SAMPLER_CREATE_INFO;
        sci.magFilter = VK_FILTER_LINEAR;
        sci.minFilter = VK_FILTER_LINEAR;
        sci.addressModeU = VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE;
        sci.addressModeV = VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE;
        sci.addressModeW = VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE;
        sci.maxLod = 0.f;
        if (vkCreateSampler(m_device, &sci, nullptr, &m_effectSampler) != VK_SUCCESS) return false;
    }

    // Allocate descriptor sets (reuse m_textureSetLayout, m_texturePool)
    auto allocAndWrite = [&](VkImageView view, VkDescriptorSet& set) -> bool {
        VkDescriptorSetAllocateInfo ai{};
        ai.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO;
        ai.descriptorPool = m_texturePool;
        ai.descriptorSetCount = 1;
        ai.pSetLayouts = &m_textureSetLayout;
        if (vkAllocateDescriptorSets(m_device, &ai, &set) != VK_SUCCESS) return false;

        VkDescriptorImageInfo imgInfo{m_effectSampler, view, VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL};
        VkWriteDescriptorSet  w{};
        w.sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
        w.dstSet = set;
        w.dstBinding = 0;
        w.descriptorCount = 1;
        w.descriptorType = VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER;
        w.pImageInfo = &imgInfo;
        vkUpdateDescriptorSets(m_device, 1, &w, 0, nullptr);
        return true;
    };
    if (!allocAndWrite(m_pingView, m_pingSrcSet)) return false;
    if (!allocAndWrite(m_pongView, m_pongSrcSet)) return false;

    // 4× MSAA scratch image (transient attachment for effect geometry anti-aliasing)
    {
        VkImageCreateInfo ici{};
        ici.sType = VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO;
        ici.imageType = VK_IMAGE_TYPE_2D;
        ici.format = m_swapFormat;
        ici.extent = {m_swapExtent.width, m_swapExtent.height, 1};
        ici.mipLevels = 1;
        ici.arrayLayers = 1;
        ici.samples = VK_SAMPLE_COUNT_4_BIT;
        ici.tiling = VK_IMAGE_TILING_OPTIMAL;
        ici.usage = VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT | VK_IMAGE_USAGE_TRANSIENT_ATTACHMENT_BIT;
        ici.sharingMode = VK_SHARING_MODE_EXCLUSIVE;
        ici.initialLayout = VK_IMAGE_LAYOUT_UNDEFINED;
        if (vkCreateImage(m_device, &ici, nullptr, &m_effectMsaaImage) != VK_SUCCESS) return false;

        VkMemoryRequirements req;
        vkGetImageMemoryRequirements(m_device, m_effectMsaaImage, &req);
        VkMemoryAllocateInfo ai{};
        ai.sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
        ai.allocationSize = req.size;
        ai.memoryTypeIndex = fm(req.memoryTypeBits, VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT);
        if (vkAllocateMemory(m_device, &ai, nullptr, &m_effectMsaaMemory) != VK_SUCCESS) return false;
        vkBindImageMemory(m_device, m_effectMsaaImage, m_effectMsaaMemory, 0);

        VkImageViewCreateInfo ivci{};
        ivci.sType = VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO;
        ivci.image = m_effectMsaaImage;
        ivci.viewType = VK_IMAGE_VIEW_TYPE_2D;
        ivci.format = m_swapFormat;
        ivci.subresourceRange = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1};
        if (vkCreateImageView(m_device, &ivci, nullptr, &m_effectMsaaView) != VK_SUCCESS) return false;
    }

    // Geometry render pass: 4× MSAA → resolve directly into ping (1×)
    {
        VkAttachmentDescription atts[2]{};
        // 0: MSAA color (cleared, discarded after resolve)
        atts[0].format = m_swapFormat;
        atts[0].samples = VK_SAMPLE_COUNT_4_BIT;
        atts[0].loadOp = VK_ATTACHMENT_LOAD_OP_CLEAR;
        atts[0].storeOp = VK_ATTACHMENT_STORE_OP_DONT_CARE;
        atts[0].stencilLoadOp = VK_ATTACHMENT_LOAD_OP_DONT_CARE;
        atts[0].stencilStoreOp = VK_ATTACHMENT_STORE_OP_DONT_CARE;
        atts[0].initialLayout = VK_IMAGE_LAYOUT_UNDEFINED;
        atts[0].finalLayout = VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL;
        // 1: Resolve target = ping (1×), final layout for shader read
        atts[1].format = m_swapFormat;
        atts[1].samples = VK_SAMPLE_COUNT_1_BIT;
        atts[1].loadOp = VK_ATTACHMENT_LOAD_OP_DONT_CARE;
        atts[1].storeOp = VK_ATTACHMENT_STORE_OP_STORE;
        atts[1].stencilLoadOp = VK_ATTACHMENT_LOAD_OP_DONT_CARE;
        atts[1].stencilStoreOp = VK_ATTACHMENT_STORE_OP_DONT_CARE;
        atts[1].initialLayout = VK_IMAGE_LAYOUT_UNDEFINED;
        atts[1].finalLayout = VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL;

        VkAttachmentReference colorRef{0, VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL};
        VkAttachmentReference resolveRef{1, VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL};

        VkSubpassDescription sub{};
        sub.pipelineBindPoint = VK_PIPELINE_BIND_POINT_GRAPHICS;
        sub.colorAttachmentCount = 1;
        sub.pColorAttachments = &colorRef;
        sub.pResolveAttachments = &resolveRef;

        // RAW: resolve write → subsequent fragment shader reads of ping
        VkSubpassDependency dep{};
        dep.srcSubpass = 0;
        dep.dstSubpass = VK_SUBPASS_EXTERNAL;
        dep.srcStageMask = VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT;
        dep.srcAccessMask = VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT;
        dep.dstStageMask = VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT;
        dep.dstAccessMask = VK_ACCESS_SHADER_READ_BIT;

        VkRenderPassCreateInfo rpci{};
        rpci.sType = VK_STRUCTURE_TYPE_RENDER_PASS_CREATE_INFO;
        rpci.attachmentCount = 2;
        rpci.pAttachments = atts;
        rpci.subpassCount = 1;
        rpci.pSubpasses = &sub;
        rpci.dependencyCount = 1;
        rpci.pDependencies = &dep;
        if (vkCreateRenderPass(m_device, &rpci, nullptr, &m_effectGeomPass) != VK_SUCCESS) return false;
    }

    // Geometry framebuffer: [msaaView, pingView]
    {
        VkImageView             attachments[2] = {m_effectMsaaView, m_pingView};
        VkFramebufferCreateInfo fci{};
        fci.sType = VK_STRUCTURE_TYPE_FRAMEBUFFER_CREATE_INFO;
        fci.renderPass = m_effectGeomPass;
        fci.attachmentCount = 2;
        fci.pAttachments = attachments;
        fci.width = m_swapExtent.width;
        fci.height = m_swapExtent.height;
        fci.layers = 1;
        if (vkCreateFramebuffer(m_device, &fci, nullptr, &m_effectGeomFb) != VK_SUCCESS) return false;
    }

    // 4× MSAA geometry pipeline for effect ping pass
    {
        auto vertSpv = compileGLSL(loadShaderSource("vert.glsl"), VK_SHADER_STAGE_VERTEX_BIT);
        auto fragSpv = compileGLSL(loadShaderSource("frag.glsl"), VK_SHADER_STAGE_FRAGMENT_BIT);
        if (vertSpv.empty() || fragSpv.empty()) return false;

        VkShaderModule vert = createShaderModule(vertSpv);
        VkShaderModule frag = createShaderModule(fragSpv);

        VkPipelineShaderStageCreateInfo stages[2]{};
        stages[0] = {VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO, nullptr, 0, VK_SHADER_STAGE_VERTEX_BIT, vert, "main", nullptr};
        stages[1] = {VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO, nullptr, 0, VK_SHADER_STAGE_FRAGMENT_BIT, frag, "main", nullptr};

        VkVertexInputBindingDescription   binding{0, sizeof(Vertex), VK_VERTEX_INPUT_RATE_VERTEX};
        VkVertexInputAttributeDescription attrs[4]{};
        attrs[0] = {0, 0, VK_FORMAT_R32G32_SFLOAT, offsetof(Vertex, pos)};
        attrs[1] = {1, 0, VK_FORMAT_R32G32_SFLOAT, offsetof(Vertex, uv)};
        attrs[2] = {2, 0, VK_FORMAT_R32G32B32A32_SFLOAT, offsetof(Vertex, color)};
        attrs[3] = {3, 0, VK_FORMAT_R32G32B32A32_SFLOAT, offsetof(Vertex, extra)};

        VkPipelineVertexInputStateCreateInfo vi{};
        vi.sType = VK_STRUCTURE_TYPE_PIPELINE_VERTEX_INPUT_STATE_CREATE_INFO;
        vi.vertexBindingDescriptionCount = 1;
        vi.pVertexBindingDescriptions = &binding;
        vi.vertexAttributeDescriptionCount = 4;
        vi.pVertexAttributeDescriptions = attrs;

        VkPipelineInputAssemblyStateCreateInfo ia{};
        ia.sType = VK_STRUCTURE_TYPE_PIPELINE_INPUT_ASSEMBLY_STATE_CREATE_INFO;
        ia.topology = VK_PRIMITIVE_TOPOLOGY_TRIANGLE_LIST;

        VkDynamicState                   dynStates[] = {VK_DYNAMIC_STATE_VIEWPORT, VK_DYNAMIC_STATE_SCISSOR};
        VkPipelineDynamicStateCreateInfo dyn{};
        dyn.sType = VK_STRUCTURE_TYPE_PIPELINE_DYNAMIC_STATE_CREATE_INFO;
        dyn.dynamicStateCount = 2;
        dyn.pDynamicStates = dynStates;

        VkPipelineViewportStateCreateInfo vs{};
        vs.sType = VK_STRUCTURE_TYPE_PIPELINE_VIEWPORT_STATE_CREATE_INFO;
        vs.viewportCount = 1;
        vs.scissorCount = 1;

        VkPipelineRasterizationStateCreateInfo rs{};
        rs.sType = VK_STRUCTURE_TYPE_PIPELINE_RASTERIZATION_STATE_CREATE_INFO;
        rs.polygonMode = VK_POLYGON_MODE_FILL;
        rs.cullMode = VK_CULL_MODE_NONE;
        rs.frontFace = VK_FRONT_FACE_CLOCKWISE;
        rs.lineWidth = 1.0f;

        VkPipelineMultisampleStateCreateInfo ms{};
        ms.sType = VK_STRUCTURE_TYPE_PIPELINE_MULTISAMPLE_STATE_CREATE_INFO;
        ms.rasterizationSamples = VK_SAMPLE_COUNT_4_BIT;

        VkPipelineColorBlendAttachmentState blendA{};
        blendA.blendEnable = VK_TRUE;
        blendA.srcColorBlendFactor = VK_BLEND_FACTOR_SRC_ALPHA;
        blendA.dstColorBlendFactor = VK_BLEND_FACTOR_ONE_MINUS_SRC_ALPHA;
        blendA.colorBlendOp = VK_BLEND_OP_ADD;
        blendA.srcAlphaBlendFactor = VK_BLEND_FACTOR_ONE;
        blendA.dstAlphaBlendFactor = VK_BLEND_FACTOR_ONE_MINUS_SRC_ALPHA;
        blendA.alphaBlendOp = VK_BLEND_OP_ADD;
        blendA.colorWriteMask = VK_COLOR_COMPONENT_R_BIT | VK_COLOR_COMPONENT_G_BIT |
                                VK_COLOR_COMPONENT_B_BIT | VK_COLOR_COMPONENT_A_BIT;

        VkPipelineColorBlendStateCreateInfo blend{};
        blend.sType = VK_STRUCTURE_TYPE_PIPELINE_COLOR_BLEND_STATE_CREATE_INFO;
        blend.attachmentCount = 1;
        blend.pAttachments = &blendA;

        VkGraphicsPipelineCreateInfo gpci{};
        gpci.sType = VK_STRUCTURE_TYPE_GRAPHICS_PIPELINE_CREATE_INFO;
        gpci.stageCount = 2;
        gpci.pStages = stages;
        gpci.pVertexInputState = &vi;
        gpci.pInputAssemblyState = &ia;
        gpci.pViewportState = &vs;
        gpci.pRasterizationState = &rs;
        gpci.pMultisampleState = &ms;
        gpci.pColorBlendState = &blend;
        gpci.pDynamicState = &dyn;
        gpci.layout = m_pipelineLayout;
        gpci.renderPass = m_effectGeomPass;

        bool ok = vkCreateGraphicsPipelines(m_device, VK_NULL_HANDLE, 1, &gpci, nullptr, &m_effectGeomPipeline) == VK_SUCCESS;
        vkDestroyShaderModule(m_device, vert, nullptr);
        vkDestroyShaderModule(m_device, frag, nullptr);
        if (!ok) return false;
    }

    // 1-sample blend-mode pipelines for adjustment-layer flatten passes. The
    // flatten composites MANY meshes (each with its own blend mode) into the
    // 1-sample ping via m_effectPass — so, unlike the headless renderer, we
    // cannot reuse the 4× MSAA main m_pipelines[] here (incompatible sample
    // count) nor the single-mode m_effectGeomPipeline. This array is
    // m_pipelines[] rebuilt at 1 sample against m_effectPass. Same vert/frag as
    // the main scene, so composite quads (draw mode 3) and geometry both work.
    {
        auto vertSpv = compileGLSL(loadShaderSource("vert.glsl"), VK_SHADER_STAGE_VERTEX_BIT);
        auto fragSpv = compileGLSL(loadShaderSource("frag.glsl"), VK_SHADER_STAGE_FRAGMENT_BIT);
        if (vertSpv.empty() || fragSpv.empty()) return false;

        VkShaderModule vert = createShaderModule(vertSpv);
        VkShaderModule frag = createShaderModule(fragSpv);

        VkPipelineShaderStageCreateInfo stages[2]{};
        stages[0] = {VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO, nullptr, 0, VK_SHADER_STAGE_VERTEX_BIT, vert, "main", nullptr};
        stages[1] = {VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO, nullptr, 0, VK_SHADER_STAGE_FRAGMENT_BIT, frag, "main", nullptr};

        VkVertexInputBindingDescription   binding{0, sizeof(Vertex), VK_VERTEX_INPUT_RATE_VERTEX};
        VkVertexInputAttributeDescription attrs[4]{};
        attrs[0] = {0, 0, VK_FORMAT_R32G32_SFLOAT, offsetof(Vertex, pos)};
        attrs[1] = {1, 0, VK_FORMAT_R32G32_SFLOAT, offsetof(Vertex, uv)};
        attrs[2] = {2, 0, VK_FORMAT_R32G32B32A32_SFLOAT, offsetof(Vertex, color)};
        attrs[3] = {3, 0, VK_FORMAT_R32G32B32A32_SFLOAT, offsetof(Vertex, extra)};

        VkPipelineVertexInputStateCreateInfo vi{};
        vi.sType = VK_STRUCTURE_TYPE_PIPELINE_VERTEX_INPUT_STATE_CREATE_INFO;
        vi.vertexBindingDescriptionCount = 1;
        vi.pVertexBindingDescriptions = &binding;
        vi.vertexAttributeDescriptionCount = 4;
        vi.pVertexAttributeDescriptions = attrs;

        VkPipelineInputAssemblyStateCreateInfo ia{};
        ia.sType = VK_STRUCTURE_TYPE_PIPELINE_INPUT_ASSEMBLY_STATE_CREATE_INFO;
        ia.topology = VK_PRIMITIVE_TOPOLOGY_TRIANGLE_LIST;

        VkDynamicState                   dynStates[] = {VK_DYNAMIC_STATE_VIEWPORT, VK_DYNAMIC_STATE_SCISSOR};
        VkPipelineDynamicStateCreateInfo dyn{};
        dyn.sType = VK_STRUCTURE_TYPE_PIPELINE_DYNAMIC_STATE_CREATE_INFO;
        dyn.dynamicStateCount = 2;
        dyn.pDynamicStates = dynStates;

        VkPipelineViewportStateCreateInfo vs{};
        vs.sType = VK_STRUCTURE_TYPE_PIPELINE_VIEWPORT_STATE_CREATE_INFO;
        vs.viewportCount = 1;
        vs.scissorCount = 1;

        VkPipelineRasterizationStateCreateInfo rs{};
        rs.sType = VK_STRUCTURE_TYPE_PIPELINE_RASTERIZATION_STATE_CREATE_INFO;
        rs.polygonMode = VK_POLYGON_MODE_FILL;
        rs.cullMode = VK_CULL_MODE_NONE;
        rs.frontFace = VK_FRONT_FACE_CLOCKWISE;
        rs.lineWidth = 1.0f;

        VkPipelineMultisampleStateCreateInfo ms{};
        ms.sType = VK_STRUCTURE_TYPE_PIPELINE_MULTISAMPLE_STATE_CREATE_INFO;
        ms.rasterizationSamples = VK_SAMPLE_COUNT_1_BIT; // m_effectPass is 1-sample

        VkPipelineColorBlendAttachmentState blendAttach[kBlendModeCount];
        VkPipelineColorBlendStateCreateInfo blendState[kBlendModeCount]{};
        for (int m = 0; m < kBlendModeCount; ++m) {
            blendAttach[m] = blendAttachmentFor(m);
            blendState[m].sType = VK_STRUCTURE_TYPE_PIPELINE_COLOR_BLEND_STATE_CREATE_INFO;
            blendState[m].attachmentCount = 1;
            blendState[m].pAttachments = &blendAttach[m];
        }

        VkGraphicsPipelineCreateInfo cis[kBlendModeCount]{};
        for (int m = 0; m < kBlendModeCount; ++m) {
            cis[m].sType = VK_STRUCTURE_TYPE_GRAPHICS_PIPELINE_CREATE_INFO;
            cis[m].stageCount = 2;
            cis[m].pStages = stages;
            cis[m].pVertexInputState = &vi;
            cis[m].pInputAssemblyState = &ia;
            cis[m].pViewportState = &vs;
            cis[m].pRasterizationState = &rs;
            cis[m].pMultisampleState = &ms;
            cis[m].pColorBlendState = &blendState[m];
            cis[m].pDynamicState = &dyn;
            cis[m].layout = m_pipelineLayout;
            cis[m].renderPass = m_effectPass;
        }

        bool ok = vkCreateGraphicsPipelines(m_device, VK_NULL_HANDLE, kBlendModeCount, cis, nullptr, m_effectBlendPipelines) == VK_SUCCESS;
        vkDestroyShaderModule(m_device, vert, nullptr);
        vkDestroyShaderModule(m_device, frag, nullptr);
        if (!ok) return false;
    }

    // Effect kernel pipelines — scan assets/shaders/*/frag.glsl automatically
    {
        std::filesystem::path shadersDir(std::string(SHADER_DIR));
        for (const auto& entry : std::filesystem::directory_iterator(shadersDir)) {
            if (!entry.is_directory()) continue;
            std::string dirName = entry.path().filename().string();
            // Skip non-effect dirs (geometry shaders, fullscreen quad vert).
            // "glow" is skipped: its frag is the additive-combine half of a
            // hand-built two-stage pass (blendEnable + LOAD render pass), built
            // separately by createGlowResources() — not a generic single-pass effect.
            // "matte" is skipped too: its frag samples TWO textures, so it needs
            // the hand-built 2-sampler layout/pipeline from createMatteResources().
            // "lut" is skipped too: its frag samples TWO textures (content + LUT
            // atlas), so it uses the hand-built 2-sampler layout/pipeline from
            // createLutResources(), not the generic single-sampler path.
            if (dirName == "effects" || dirName == "quadraticBezier" || dirName == "glow" || dirName == "matte" || dirName == "lut") continue;
            if (std::filesystem::exists(entry.path() / "frag.glsl"))
                createEffectPipeline(dirName);
        }
    }

    if (!createGlowResources()) return false;
    if (!createMatteResources()) return false;
    if (!createLutResources()) return false;

    // Static composite quad
    {
        Vertex verts[4] = {
            {{-1.f, -1.f}, {0.f, 0.f}, {0.f, 0.f, 0.f, 1.f}, {3.f, 0.f, 0.f, 0.f}},
            {{1.f, -1.f}, {1.f, 0.f}, {0.f, 0.f, 0.f, 1.f}, {3.f, 0.f, 0.f, 0.f}},
            {{1.f, 1.f}, {1.f, 1.f}, {0.f, 0.f, 0.f, 1.f}, {3.f, 0.f, 0.f, 0.f}},
            {{-1.f, 1.f}, {0.f, 1.f}, {0.f, 0.f, 0.f, 1.f}, {3.f, 0.f, 0.f, 0.f}},
        };
        uint32_t idx[6] = {0, 1, 2, 0, 2, 3};

        auto upload = [&](const void* data, VkDeviceSize sz, VkBufferUsageFlags usage,
                          VkBuffer& buf, VkDeviceMemory& mem) -> bool {
            VkBufferCreateInfo bi{};
            bi.sType = VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO;
            bi.size = sz;
            bi.usage = usage;
            bi.sharingMode = VK_SHARING_MODE_EXCLUSIVE;
            if (vkCreateBuffer(m_device, &bi, nullptr, &buf) != VK_SUCCESS) return false;

            VkMemoryRequirements req;
            vkGetBufferMemoryRequirements(m_device, buf, &req);
            VkMemoryAllocateInfo ai{};
            ai.sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
            ai.allocationSize = req.size;
            ai.memoryTypeIndex = fm(req.memoryTypeBits, VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT);
            if (vkAllocateMemory(m_device, &ai, nullptr, &mem) != VK_SUCCESS) return false;
            vkBindBufferMemory(m_device, buf, mem, 0);

            void* mapped;
            vkMapMemory(m_device, mem, 0, sz, 0, &mapped);
            memcpy(mapped, data, sz);
            vkUnmapMemory(m_device, mem);
            return true;
        };

        if (!upload(verts, sizeof(verts), VK_BUFFER_USAGE_VERTEX_BUFFER_BIT, m_compVtxBuf, m_compVtxMem)) return false;
        if (!upload(idx, sizeof(idx), VK_BUFFER_USAGE_INDEX_BUFFER_BIT, m_compIdxBuf, m_compIdxMem)) return false;
    }

    return true;
}

// ===========================================================================
// ensureEffectResultCapacity — grow the per-effect-mesh result image pool
// ===========================================================================

bool VC::VulkanWidget::ensureEffectResultCapacity(size_t count)
{
    auto fm = [this](uint32_t f, VkMemoryPropertyFlags p) { return findMemoryType(f, p); };

    while (m_effectResults.size() < count) {
        EffectResultSlot slot{};

        VkImageCreateInfo ici{};
        ici.sType = VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO;
        ici.imageType = VK_IMAGE_TYPE_2D;
        ici.format = m_swapFormat;
        ici.extent = {m_swapExtent.width, m_swapExtent.height, 1};
        ici.mipLevels = 1;
        ici.arrayLayers = 1;
        ici.samples = VK_SAMPLE_COUNT_1_BIT;
        ici.tiling = VK_IMAGE_TILING_OPTIMAL;
        ici.usage = VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT | VK_IMAGE_USAGE_SAMPLED_BIT;
        ici.sharingMode = VK_SHARING_MODE_EXCLUSIVE;
        ici.initialLayout = VK_IMAGE_LAYOUT_UNDEFINED;
        if (vkCreateImage(m_device, &ici, nullptr, &slot.image) != VK_SUCCESS) return false;

        VkMemoryRequirements req;
        vkGetImageMemoryRequirements(m_device, slot.image, &req);
        VkMemoryAllocateInfo ai{};
        ai.sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
        ai.allocationSize = req.size;
        ai.memoryTypeIndex = fm(req.memoryTypeBits, VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT);
        if (vkAllocateMemory(m_device, &ai, nullptr, &slot.memory) != VK_SUCCESS) return false;
        vkBindImageMemory(m_device, slot.image, slot.memory, 0);

        VkImageViewCreateInfo ivci{};
        ivci.sType = VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO;
        ivci.image = slot.image;
        ivci.viewType = VK_IMAGE_VIEW_TYPE_2D;
        ivci.format = m_swapFormat;
        ivci.subresourceRange = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1};
        if (vkCreateImageView(m_device, &ivci, nullptr, &slot.view) != VK_SUCCESS) return false;

        VkFramebufferCreateInfo fci{};
        fci.sType = VK_STRUCTURE_TYPE_FRAMEBUFFER_CREATE_INFO;
        fci.renderPass = m_effectPass;
        fci.attachmentCount = 1;
        fci.pAttachments = &slot.view;
        fci.width = m_swapExtent.width;
        fci.height = m_swapExtent.height;
        fci.layers = 1;
        if (vkCreateFramebuffer(m_device, &fci, nullptr, &slot.framebuffer) != VK_SUCCESS) return false;

        VkDescriptorSetAllocateInfo ai2{};
        ai2.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO;
        ai2.descriptorPool = m_texturePool;
        ai2.descriptorSetCount = 1;
        ai2.pSetLayouts = &m_textureSetLayout;
        if (vkAllocateDescriptorSets(m_device, &ai2, &slot.descriptorSet) != VK_SUCCESS) return false;

        VkDescriptorImageInfo imgInfo{m_effectSampler, slot.view, VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL};
        VkWriteDescriptorSet  w{};
        w.sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
        w.dstSet = slot.descriptorSet;
        w.dstBinding = 0;
        w.descriptorCount = 1;
        w.descriptorType = VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER;
        w.pImageInfo = &imgInfo;
        vkUpdateDescriptorSets(m_device, 1, &w, 0, nullptr);

        m_effectResults.push_back(slot);
    }
    return true;
}

bool VC::VulkanWidget::createEffectPipeline(const std::string& name)
{
    std::string lower = name;
    std::transform(lower.begin(), lower.end(), lower.begin(), ::tolower);

    auto fragSrc = loadEffectShader(lower, "frag.glsl");
    if (fragSrc.empty()) return false;

    return createEffectPipelineFromSource(lower, fragSrc);
}

// Cache key for a runtime-loaded MathShader pipeline — see the headless
// renderer's mathPipelineKey for the full rationale (namespaced against
// folder-name collisions, pre-lowercased to survive recordEffectKernelPass's
// name transform; only the KEY is lowercased, the file is read as given).
static std::string mathPipelineKey(const std::string& path)
{
    std::string key = "math:" + path;
    std::transform(key.begin(), key.end(), key.begin(), ::tolower);
    return key;
}

// MathShader pipelines: user-supplied fragment GLSL (eff.strParam is the file
// path), compiled once per file into m_effectPipelines. Failures are logged
// once and remembered (m_mathFailed) so a broken file doesn't recompile every
// frame — mirrors VulkanHeadlessRenderer::ensureMathPipeline exactly.
bool VC::VulkanWidget::ensureMathPipeline(const std::string& path)
{
    std::string key = mathPipelineKey(path);
    if (m_effectPipelines.count(key)) return true;
    if (m_mathFailed.count(key)) return false;

    std::ifstream f(path);
    std::string   fragSrc;
    if (f.is_open()) {
        std::ostringstream ss;
        ss << f.rdbuf();
        fragSrc = ss.str();
    }

    if (fragSrc.empty() || !createEffectPipelineFromSource(key, fragSrc)) {
        std::cerr << "[mathShader] could not load/compile '" << path
                  << "' — effect skipped (fix the file and rerun)." << std::endl;
        m_mathFailed.insert(key);
        return false;
    }
    return true;
}

bool VC::VulkanWidget::createEffectPipelineFromSource(const std::string& key, const std::string& fragSrc)
{
    auto vertSrc = loadEffectShader("effects", "vert.glsl");
    if (vertSrc.empty()) return false;

    auto vertSpv = compileGLSL(vertSrc, VK_SHADER_STAGE_VERTEX_BIT);
    auto fragSpv = compileGLSL(fragSrc, VK_SHADER_STAGE_FRAGMENT_BIT);
    if (vertSpv.empty() || fragSpv.empty()) return false;

    VkPushConstantRange pcRange{};
    pcRange.stageFlags = VK_SHADER_STAGE_FRAGMENT_BIT;
    pcRange.offset = 0;
    pcRange.size = sizeof(EffectPC);

    EffectPipeline             ep{};
    VkPipelineLayoutCreateInfo plci{};
    plci.sType = VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO;
    plci.setLayoutCount = 1;
    plci.pSetLayouts = &m_textureSetLayout;
    plci.pushConstantRangeCount = 1;
    plci.pPushConstantRanges = &pcRange;
    if (vkCreatePipelineLayout(m_device, &plci, nullptr, &ep.layout) != VK_SUCCESS) return false;

    VkShaderModule vert = createShaderModule(vertSpv);
    VkShaderModule frag = createShaderModule(fragSpv);

    VkPipelineShaderStageCreateInfo stages[2]{};
    stages[0] = {VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO, nullptr, 0, VK_SHADER_STAGE_VERTEX_BIT, vert, "main", nullptr};
    stages[1] = {VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO, nullptr, 0, VK_SHADER_STAGE_FRAGMENT_BIT, frag, "main", nullptr};

    VkPipelineVertexInputStateCreateInfo   vi{VK_STRUCTURE_TYPE_PIPELINE_VERTEX_INPUT_STATE_CREATE_INFO};
    VkPipelineInputAssemblyStateCreateInfo ia{VK_STRUCTURE_TYPE_PIPELINE_INPUT_ASSEMBLY_STATE_CREATE_INFO};
    ia.topology = VK_PRIMITIVE_TOPOLOGY_TRIANGLE_LIST;

    VkDynamicState                   dynStates[] = {VK_DYNAMIC_STATE_VIEWPORT, VK_DYNAMIC_STATE_SCISSOR};
    VkPipelineDynamicStateCreateInfo dyn{VK_STRUCTURE_TYPE_PIPELINE_DYNAMIC_STATE_CREATE_INFO};
    dyn.dynamicStateCount = 2;
    dyn.pDynamicStates = dynStates;

    VkPipelineViewportStateCreateInfo vs{VK_STRUCTURE_TYPE_PIPELINE_VIEWPORT_STATE_CREATE_INFO};
    vs.viewportCount = 1;
    vs.scissorCount = 1;

    VkPipelineRasterizationStateCreateInfo rs{VK_STRUCTURE_TYPE_PIPELINE_RASTERIZATION_STATE_CREATE_INFO};
    rs.polygonMode = VK_POLYGON_MODE_FILL;
    rs.cullMode = VK_CULL_MODE_NONE;
    rs.frontFace = VK_FRONT_FACE_CLOCKWISE;
    rs.lineWidth = 1.0f;

    VkPipelineMultisampleStateCreateInfo ms{VK_STRUCTURE_TYPE_PIPELINE_MULTISAMPLE_STATE_CREATE_INFO};
    ms.rasterizationSamples = VK_SAMPLE_COUNT_1_BIT;

    VkPipelineColorBlendAttachmentState blendA{};
    blendA.blendEnable = VK_FALSE;
    blendA.colorWriteMask = VK_COLOR_COMPONENT_R_BIT | VK_COLOR_COMPONENT_G_BIT |
                            VK_COLOR_COMPONENT_B_BIT | VK_COLOR_COMPONENT_A_BIT;

    VkPipelineColorBlendStateCreateInfo blend{VK_STRUCTURE_TYPE_PIPELINE_COLOR_BLEND_STATE_CREATE_INFO};
    blend.attachmentCount = 1;
    blend.pAttachments = &blendA;

    VkGraphicsPipelineCreateInfo gpci{};
    gpci.sType = VK_STRUCTURE_TYPE_GRAPHICS_PIPELINE_CREATE_INFO;
    gpci.stageCount = 2;
    gpci.pStages = stages;
    gpci.pVertexInputState = &vi;
    gpci.pInputAssemblyState = &ia;
    gpci.pViewportState = &vs;
    gpci.pRasterizationState = &rs;
    gpci.pMultisampleState = &ms;
    gpci.pColorBlendState = &blend;
    gpci.pDynamicState = &dyn;
    gpci.layout = ep.layout;
    gpci.renderPass = m_effectPass;

    bool ok = vkCreateGraphicsPipelines(m_device, VK_NULL_HANDLE, 1, &gpci, nullptr, &ep.pipeline) == VK_SUCCESS;
    vkDestroyShaderModule(m_device, vert, nullptr);
    vkDestroyShaderModule(m_device, frag, nullptr);

    if (!ok) {
        vkDestroyPipelineLayout(m_device, ep.layout, nullptr);
        return false;
    }
    m_effectPipelines[key] = ep;
    return true;
}

// ============================================================================
// createGlowResources — glow-only extras (LOAD render pass, third scratch
// buffer, additive-combine pipeline). Mirrors the headless renderer; kept out
// of the generic effect path because none of it fits the single-sampler /
// CLEAR / blend-disabled shape.
// ============================================================================
bool VC::VulkanWidget::createGlowResources()
{
    auto fm = [this](uint32_t f, VkMemoryPropertyFlags p) { return findMemoryType(f, p); };

    // Third scratch buffer: holds the preserved sharp original across blur.
    {
        VkImageCreateInfo ici{};
        ici.sType = VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO;
        ici.imageType = VK_IMAGE_TYPE_2D;
        ici.format = m_swapFormat;
        ici.extent = {m_swapExtent.width, m_swapExtent.height, 1};
        ici.mipLevels = 1;
        ici.arrayLayers = 1;
        ici.samples = VK_SAMPLE_COUNT_1_BIT;
        ici.tiling = VK_IMAGE_TILING_OPTIMAL;
        ici.usage = VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT | VK_IMAGE_USAGE_SAMPLED_BIT;
        ici.sharingMode = VK_SHARING_MODE_EXCLUSIVE;
        ici.initialLayout = VK_IMAGE_LAYOUT_UNDEFINED;
        if (vkCreateImage(m_device, &ici, nullptr, &m_thirdImage) != VK_SUCCESS) return false;

        VkMemoryRequirements req;
        vkGetImageMemoryRequirements(m_device, m_thirdImage, &req);
        VkMemoryAllocateInfo ai{};
        ai.sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
        ai.allocationSize = req.size;
        ai.memoryTypeIndex = fm(req.memoryTypeBits, VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT);
        if (vkAllocateMemory(m_device, &ai, nullptr, &m_thirdMemory) != VK_SUCCESS) return false;
        vkBindImageMemory(m_device, m_thirdImage, m_thirdMemory, 0);

        VkImageViewCreateInfo ivci{};
        ivci.sType = VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO;
        ivci.image = m_thirdImage;
        ivci.viewType = VK_IMAGE_VIEW_TYPE_2D;
        ivci.format = m_swapFormat;
        ivci.subresourceRange = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1};
        if (vkCreateImageView(m_device, &ivci, nullptr, &m_thirdView) != VK_SUCCESS) return false;
    }

    // LOAD render pass: identical to m_effectPass but loadOp = LOAD and
    // initialLayout = SHADER_READ_ONLY_OPTIMAL. Framebuffer compatibility is by
    // format/sample-count only, so P5 reuses the ping/pong framebuffers.
    {
        VkAttachmentDescription att{};
        att.format = m_swapFormat;
        att.samples = VK_SAMPLE_COUNT_1_BIT;
        att.loadOp = VK_ATTACHMENT_LOAD_OP_LOAD;
        att.storeOp = VK_ATTACHMENT_STORE_OP_STORE;
        att.stencilLoadOp = VK_ATTACHMENT_LOAD_OP_DONT_CARE;
        att.stencilStoreOp = VK_ATTACHMENT_STORE_OP_DONT_CARE;
        att.initialLayout = VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL;
        att.finalLayout = VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL;

        VkAttachmentReference ref{0, VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL};

        VkSubpassDescription sub{};
        sub.pipelineBindPoint = VK_PIPELINE_BIND_POINT_GRAPHICS;
        sub.colorAttachmentCount = 1;
        sub.pColorAttachments = &ref;

        VkSubpassDependency deps[2]{};
        deps[0].srcSubpass = 0;
        deps[0].dstSubpass = VK_SUBPASS_EXTERNAL;
        deps[0].srcStageMask = VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT;
        deps[0].srcAccessMask = VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT;
        deps[0].dstStageMask = VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT;
        deps[0].dstAccessMask = VK_ACCESS_SHADER_READ_BIT;
        deps[1].srcSubpass = VK_SUBPASS_EXTERNAL;
        deps[1].dstSubpass = 0;
        deps[1].srcStageMask = VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT;
        deps[1].srcAccessMask = VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT;
        deps[1].dstStageMask = VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT;
        deps[1].dstAccessMask = VK_ACCESS_COLOR_ATTACHMENT_READ_BIT | VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT;

        VkRenderPassCreateInfo rpci{};
        rpci.sType = VK_STRUCTURE_TYPE_RENDER_PASS_CREATE_INFO;
        rpci.attachmentCount = 1;
        rpci.pAttachments = &att;
        rpci.subpassCount = 1;
        rpci.pSubpasses = &sub;
        rpci.dependencyCount = 2;
        rpci.pDependencies = deps;
        if (vkCreateRenderPass(m_device, &rpci, nullptr, &m_effectPassLoad) != VK_SUCCESS) return false;
    }

    // Third framebuffer (built against m_effectPass — only ever a CLEAR target).
    {
        VkFramebufferCreateInfo fci{};
        fci.sType = VK_STRUCTURE_TYPE_FRAMEBUFFER_CREATE_INFO;
        fci.renderPass = m_effectPass;
        fci.attachmentCount = 1;
        fci.pAttachments = &m_thirdView;
        fci.width = m_swapExtent.width;
        fci.height = m_swapExtent.height;
        fci.layers = 1;
        if (vkCreateFramebuffer(m_device, &fci, nullptr, &m_thirdFb) != VK_SUCCESS) return false;
    }

    // Descriptor set reading the third buffer.
    {
        VkDescriptorSetAllocateInfo ai{};
        ai.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO;
        ai.descriptorPool = m_texturePool;
        ai.descriptorSetCount = 1;
        ai.pSetLayouts = &m_textureSetLayout;
        if (vkAllocateDescriptorSets(m_device, &ai, &m_thirdSrcSet) != VK_SUCCESS) return false;

        VkDescriptorImageInfo imgInfo{m_effectSampler, m_thirdView, VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL};
        VkWriteDescriptorSet  w{};
        w.sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
        w.dstSet = m_thirdSrcSet;
        w.dstBinding = 0;
        w.descriptorCount = 1;
        w.descriptorType = VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER;
        w.pImageInfo = &imgInfo;
        vkUpdateDescriptorSets(m_device, 1, &w, 0, nullptr);
    }

    // Additive-combine pipeline: glow/frag.glsl (× intensity) + (ONE, ONE) blend
    // into m_effectPassLoad.
    {
        auto vertSrc = loadEffectShader("effects", "vert.glsl");
        auto fragSrc = loadEffectShader("glow", "frag.glsl");
        if (vertSrc.empty() || fragSrc.empty()) return false;
        auto vertSpv = compileGLSL(vertSrc, VK_SHADER_STAGE_VERTEX_BIT);
        auto fragSpv = compileGLSL(fragSrc, VK_SHADER_STAGE_FRAGMENT_BIT);
        if (vertSpv.empty() || fragSpv.empty()) return false;

        VkPushConstantRange pcRange{};
        pcRange.stageFlags = VK_SHADER_STAGE_FRAGMENT_BIT;
        pcRange.offset = 0;
        pcRange.size = sizeof(EffectPC);

        VkPipelineLayoutCreateInfo plci{};
        plci.sType = VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO;
        plci.setLayoutCount = 1;
        plci.pSetLayouts = &m_textureSetLayout;
        plci.pushConstantRangeCount = 1;
        plci.pPushConstantRanges = &pcRange;
        if (vkCreatePipelineLayout(m_device, &plci, nullptr, &m_glowCombine.layout) != VK_SUCCESS) return false;

        VkShaderModule vert = createShaderModule(vertSpv);
        VkShaderModule frag = createShaderModule(fragSpv);

        VkPipelineShaderStageCreateInfo stages[2]{};
        stages[0] = {VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO, nullptr, 0, VK_SHADER_STAGE_VERTEX_BIT, vert, "main", nullptr};
        stages[1] = {VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO, nullptr, 0, VK_SHADER_STAGE_FRAGMENT_BIT, frag, "main", nullptr};

        VkPipelineVertexInputStateCreateInfo   vi{VK_STRUCTURE_TYPE_PIPELINE_VERTEX_INPUT_STATE_CREATE_INFO};
        VkPipelineInputAssemblyStateCreateInfo ia{VK_STRUCTURE_TYPE_PIPELINE_INPUT_ASSEMBLY_STATE_CREATE_INFO};
        ia.topology = VK_PRIMITIVE_TOPOLOGY_TRIANGLE_LIST;

        VkDynamicState                   dynStates[] = {VK_DYNAMIC_STATE_VIEWPORT, VK_DYNAMIC_STATE_SCISSOR};
        VkPipelineDynamicStateCreateInfo dyn{VK_STRUCTURE_TYPE_PIPELINE_DYNAMIC_STATE_CREATE_INFO};
        dyn.dynamicStateCount = 2;
        dyn.pDynamicStates = dynStates;

        VkPipelineViewportStateCreateInfo vs{VK_STRUCTURE_TYPE_PIPELINE_VIEWPORT_STATE_CREATE_INFO};
        vs.viewportCount = 1;
        vs.scissorCount = 1;

        VkPipelineRasterizationStateCreateInfo rs{VK_STRUCTURE_TYPE_PIPELINE_RASTERIZATION_STATE_CREATE_INFO};
        rs.polygonMode = VK_POLYGON_MODE_FILL;
        rs.cullMode = VK_CULL_MODE_NONE;
        rs.frontFace = VK_FRONT_FACE_CLOCKWISE;
        rs.lineWidth = 1.0f;

        VkPipelineMultisampleStateCreateInfo ms{VK_STRUCTURE_TYPE_PIPELINE_MULTISAMPLE_STATE_CREATE_INFO};
        ms.rasterizationSamples = VK_SAMPLE_COUNT_1_BIT;

        VkPipelineColorBlendAttachmentState blendA{};
        blendA.blendEnable = VK_TRUE;
        blendA.srcColorBlendFactor = VK_BLEND_FACTOR_ONE;
        blendA.dstColorBlendFactor = VK_BLEND_FACTOR_ONE;
        blendA.colorBlendOp = VK_BLEND_OP_ADD;
        blendA.srcAlphaBlendFactor = VK_BLEND_FACTOR_ONE;
        blendA.dstAlphaBlendFactor = VK_BLEND_FACTOR_ONE;
        blendA.alphaBlendOp = VK_BLEND_OP_ADD;
        blendA.colorWriteMask = VK_COLOR_COMPONENT_R_BIT | VK_COLOR_COMPONENT_G_BIT |
                                VK_COLOR_COMPONENT_B_BIT | VK_COLOR_COMPONENT_A_BIT;

        VkPipelineColorBlendStateCreateInfo blend{VK_STRUCTURE_TYPE_PIPELINE_COLOR_BLEND_STATE_CREATE_INFO};
        blend.attachmentCount = 1;
        blend.pAttachments = &blendA;

        VkGraphicsPipelineCreateInfo gpci{};
        gpci.sType = VK_STRUCTURE_TYPE_GRAPHICS_PIPELINE_CREATE_INFO;
        gpci.stageCount = 2;
        gpci.pStages = stages;
        gpci.pVertexInputState = &vi;
        gpci.pInputAssemblyState = &ia;
        gpci.pViewportState = &vs;
        gpci.pRasterizationState = &rs;
        gpci.pMultisampleState = &ms;
        gpci.pColorBlendState = &blend;
        gpci.pDynamicState = &dyn;
        gpci.layout = m_glowCombine.layout;
        gpci.renderPass = m_effectPassLoad;

        bool ok = vkCreateGraphicsPipelines(m_device, VK_NULL_HANDLE, 1, &gpci, nullptr, &m_glowCombine.pipeline) == VK_SUCCESS;
        vkDestroyShaderModule(m_device, vert, nullptr);
        vkDestroyShaderModule(m_device, frag, nullptr);
        if (!ok) {
            vkDestroyPipelineLayout(m_device, m_glowCombine.layout, nullptr);
            m_glowCombine.layout = VK_NULL_HANDLE;
            return false;
        }
    }

    return true;
}

// ============================================================================
// createMatteResources — 2-sampler descriptor layout/pool + combine pipeline.
// Mirrors the headless renderer; first 2-sampler descriptor set here, kept out
// of the generic single-sampler effect path.
// ============================================================================
bool VC::VulkanWidget::createMatteResources()
{
    VkDescriptorSetLayoutBinding bindings[2]{};
    for (int b = 0; b < 2; ++b) {
        bindings[b].binding = b;
        bindings[b].descriptorType = VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER;
        bindings[b].descriptorCount = 1;
        bindings[b].stageFlags = VK_SHADER_STAGE_FRAGMENT_BIT;
    }
    VkDescriptorSetLayoutCreateInfo lci{VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO};
    lci.bindingCount = 2;
    lci.pBindings = bindings;
    if (vkCreateDescriptorSetLayout(m_device, &lci, nullptr, &m_matteLayout) != VK_SUCCESS) return false;

    VkDescriptorPoolSize       ps{VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER, 128};
    VkDescriptorPoolCreateInfo pci{VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO};
    pci.maxSets = 64;
    pci.poolSizeCount = 1;
    pci.pPoolSizes = &ps;
    if (vkCreateDescriptorPool(m_device, &pci, nullptr, &m_mattePool) != VK_SUCCESS) return false;

    auto vertSrc = loadEffectShader("effects", "vert.glsl");
    auto fragSrc = loadEffectShader("matte", "frag.glsl");
    if (vertSrc.empty() || fragSrc.empty()) return false;
    auto vertSpv = compileGLSL(vertSrc, VK_SHADER_STAGE_VERTEX_BIT);
    auto fragSpv = compileGLSL(fragSrc, VK_SHADER_STAGE_FRAGMENT_BIT);
    if (vertSpv.empty() || fragSpv.empty()) return false;

    VkPipelineLayoutCreateInfo plci{VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO};
    plci.setLayoutCount = 1;
    plci.pSetLayouts = &m_matteLayout;
    if (vkCreatePipelineLayout(m_device, &plci, nullptr, &m_matteCombine.layout) != VK_SUCCESS) return false;

    VkShaderModule vert = createShaderModule(vertSpv);
    VkShaderModule frag = createShaderModule(fragSpv);

    VkPipelineShaderStageCreateInfo stages[2]{};
    stages[0] = {VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO, nullptr, 0, VK_SHADER_STAGE_VERTEX_BIT, vert, "main", nullptr};
    stages[1] = {VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO, nullptr, 0, VK_SHADER_STAGE_FRAGMENT_BIT, frag, "main", nullptr};

    VkPipelineVertexInputStateCreateInfo   vi{VK_STRUCTURE_TYPE_PIPELINE_VERTEX_INPUT_STATE_CREATE_INFO};
    VkPipelineInputAssemblyStateCreateInfo ia{VK_STRUCTURE_TYPE_PIPELINE_INPUT_ASSEMBLY_STATE_CREATE_INFO};
    ia.topology = VK_PRIMITIVE_TOPOLOGY_TRIANGLE_LIST;

    VkDynamicState                   dynStates[] = {VK_DYNAMIC_STATE_VIEWPORT, VK_DYNAMIC_STATE_SCISSOR};
    VkPipelineDynamicStateCreateInfo dyn{VK_STRUCTURE_TYPE_PIPELINE_DYNAMIC_STATE_CREATE_INFO};
    dyn.dynamicStateCount = 2;
    dyn.pDynamicStates = dynStates;

    VkPipelineViewportStateCreateInfo vs{VK_STRUCTURE_TYPE_PIPELINE_VIEWPORT_STATE_CREATE_INFO};
    vs.viewportCount = 1;
    vs.scissorCount = 1;

    VkPipelineRasterizationStateCreateInfo rs{VK_STRUCTURE_TYPE_PIPELINE_RASTERIZATION_STATE_CREATE_INFO};
    rs.polygonMode = VK_POLYGON_MODE_FILL;
    rs.cullMode = VK_CULL_MODE_NONE;
    rs.frontFace = VK_FRONT_FACE_CLOCKWISE;
    rs.lineWidth = 1.0f;

    VkPipelineMultisampleStateCreateInfo ms{VK_STRUCTURE_TYPE_PIPELINE_MULTISAMPLE_STATE_CREATE_INFO};
    ms.rasterizationSamples = VK_SAMPLE_COUNT_1_BIT;

    VkPipelineColorBlendAttachmentState blendA{};
    blendA.blendEnable = VK_FALSE;
    blendA.colorWriteMask = VK_COLOR_COMPONENT_R_BIT | VK_COLOR_COMPONENT_G_BIT |
                            VK_COLOR_COMPONENT_B_BIT | VK_COLOR_COMPONENT_A_BIT;

    VkPipelineColorBlendStateCreateInfo blend{VK_STRUCTURE_TYPE_PIPELINE_COLOR_BLEND_STATE_CREATE_INFO};
    blend.attachmentCount = 1;
    blend.pAttachments = &blendA;

    VkGraphicsPipelineCreateInfo gpci{};
    gpci.sType = VK_STRUCTURE_TYPE_GRAPHICS_PIPELINE_CREATE_INFO;
    gpci.stageCount = 2;
    gpci.pStages = stages;
    gpci.pVertexInputState = &vi;
    gpci.pInputAssemblyState = &ia;
    gpci.pViewportState = &vs;
    gpci.pRasterizationState = &rs;
    gpci.pMultisampleState = &ms;
    gpci.pColorBlendState = &blend;
    gpci.pDynamicState = &dyn;
    gpci.layout = m_matteCombine.layout;
    gpci.renderPass = m_effectPass;

    bool ok = vkCreateGraphicsPipelines(m_device, VK_NULL_HANDLE, 1, &gpci, nullptr, &m_matteCombine.pipeline) == VK_SUCCESS;
    vkDestroyShaderModule(m_device, vert, nullptr);
    vkDestroyShaderModule(m_device, frag, nullptr);
    if (!ok) {
        vkDestroyPipelineLayout(m_device, m_matteCombine.layout, nullptr);
        m_matteCombine.layout = VK_NULL_HANDLE;
        return false;
    }
    return true;
}

bool VC::VulkanWidget::ensureMatteSetCapacity(size_t count)
{
    while (m_matteSets.size() < count) {
        VkDescriptorSet             set = VK_NULL_HANDLE;
        VkDescriptorSetAllocateInfo ai{VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO};
        ai.descriptorPool = m_mattePool;
        ai.descriptorSetCount = 1;
        ai.pSetLayouts = &m_matteLayout;
        if (vkAllocateDescriptorSets(m_device, &ai, &set) != VK_SUCCESS) return false;
        m_matteSets.push_back(set);
    }
    return true;
}

void VC::VulkanWidget::recordMatteCombinePass(VkCommandBuffer cb, VkFramebuffer fb, VkDescriptorSet set)
{
    VkClearValue clear = {{{0.f, 0.f, 0.f, 0.f}}};
    VkViewport   vp{0, 0, (float)m_swapExtent.width, (float)m_swapExtent.height, 0, 1};
    VkRect2D     sc{{0, 0}, m_swapExtent};

    VkRenderPassBeginInfo rpi{};
    rpi.sType = VK_STRUCTURE_TYPE_RENDER_PASS_BEGIN_INFO;
    rpi.renderPass = m_effectPass;
    rpi.framebuffer = fb;
    rpi.renderArea.extent = m_swapExtent;
    rpi.clearValueCount = 1;
    rpi.pClearValues = &clear;

    vkCmdBeginRenderPass(cb, &rpi, VK_SUBPASS_CONTENTS_INLINE);
    vkCmdSetViewport(cb, 0, 1, &vp);
    vkCmdSetScissor(cb, 0, 1, &sc);
    vkCmdBindPipeline(cb, VK_PIPELINE_BIND_POINT_GRAPHICS, m_matteCombine.pipeline);
    vkCmdBindDescriptorSets(cb, VK_PIPELINE_BIND_POINT_GRAPHICS, m_matteCombine.layout, 0, 1, &set, 0, nullptr);
    vkCmdDraw(cb, 6, 1, 0, 0);
    vkCmdEndRenderPass(cb);
}

// ============================================================================
// createLutResources — 2-sampler descriptor layout/pool + combine pipeline for
// the LUT color grade. Mirrors the headless renderer; the pipeline layout
// carries push constants (intensity + atlas size). Kept out of the generic path.
// ============================================================================
bool VC::VulkanWidget::createLutResources()
{
    VkDescriptorSetLayoutBinding bindings[2]{};
    for (int b = 0; b < 2; ++b) {
        bindings[b].binding = b;
        bindings[b].descriptorType = VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER;
        bindings[b].descriptorCount = 1;
        bindings[b].stageFlags = VK_SHADER_STAGE_FRAGMENT_BIT;
    }
    VkDescriptorSetLayoutCreateInfo lci{VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO};
    lci.bindingCount = 2;
    lci.pBindings = bindings;
    if (vkCreateDescriptorSetLayout(m_device, &lci, nullptr, &m_lutLayout) != VK_SUCCESS) return false;

    VkDescriptorPoolSize       ps{VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER, 128};
    VkDescriptorPoolCreateInfo pci{VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO};
    pci.maxSets = 64;
    pci.poolSizeCount = 1;
    pci.pPoolSizes = &ps;
    if (vkCreateDescriptorPool(m_device, &pci, nullptr, &m_lutPool) != VK_SUCCESS) return false;

    auto vertSrc = loadEffectShader("effects", "vert.glsl");
    auto fragSrc = loadEffectShader("lut", "frag.glsl");
    if (vertSrc.empty() || fragSrc.empty()) return false;
    auto vertSpv = compileGLSL(vertSrc, VK_SHADER_STAGE_VERTEX_BIT);
    auto fragSpv = compileGLSL(fragSrc, VK_SHADER_STAGE_FRAGMENT_BIT);
    if (vertSpv.empty() || fragSpv.empty()) return false;

    VkPushConstantRange pcRange{};
    pcRange.stageFlags = VK_SHADER_STAGE_FRAGMENT_BIT;
    pcRange.offset = 0;
    pcRange.size = sizeof(EffectPC);

    VkPipelineLayoutCreateInfo plci{VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO};
    plci.setLayoutCount = 1;
    plci.pSetLayouts = &m_lutLayout;
    plci.pushConstantRangeCount = 1;
    plci.pPushConstantRanges = &pcRange;
    if (vkCreatePipelineLayout(m_device, &plci, nullptr, &m_lutCombine.layout) != VK_SUCCESS) return false;

    VkShaderModule vert = createShaderModule(vertSpv);
    VkShaderModule frag = createShaderModule(fragSpv);

    VkPipelineShaderStageCreateInfo stages[2]{};
    stages[0] = {VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO, nullptr, 0, VK_SHADER_STAGE_VERTEX_BIT, vert, "main", nullptr};
    stages[1] = {VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO, nullptr, 0, VK_SHADER_STAGE_FRAGMENT_BIT, frag, "main", nullptr};

    VkPipelineVertexInputStateCreateInfo   vi{VK_STRUCTURE_TYPE_PIPELINE_VERTEX_INPUT_STATE_CREATE_INFO};
    VkPipelineInputAssemblyStateCreateInfo ia{VK_STRUCTURE_TYPE_PIPELINE_INPUT_ASSEMBLY_STATE_CREATE_INFO};
    ia.topology = VK_PRIMITIVE_TOPOLOGY_TRIANGLE_LIST;

    VkDynamicState                   dynStates[] = {VK_DYNAMIC_STATE_VIEWPORT, VK_DYNAMIC_STATE_SCISSOR};
    VkPipelineDynamicStateCreateInfo dyn{VK_STRUCTURE_TYPE_PIPELINE_DYNAMIC_STATE_CREATE_INFO};
    dyn.dynamicStateCount = 2;
    dyn.pDynamicStates = dynStates;

    VkPipelineViewportStateCreateInfo vs{VK_STRUCTURE_TYPE_PIPELINE_VIEWPORT_STATE_CREATE_INFO};
    vs.viewportCount = 1;
    vs.scissorCount = 1;

    VkPipelineRasterizationStateCreateInfo rs{VK_STRUCTURE_TYPE_PIPELINE_RASTERIZATION_STATE_CREATE_INFO};
    rs.polygonMode = VK_POLYGON_MODE_FILL;
    rs.cullMode = VK_CULL_MODE_NONE;
    rs.frontFace = VK_FRONT_FACE_CLOCKWISE;
    rs.lineWidth = 1.0f;

    VkPipelineMultisampleStateCreateInfo ms{VK_STRUCTURE_TYPE_PIPELINE_MULTISAMPLE_STATE_CREATE_INFO};
    ms.rasterizationSamples = VK_SAMPLE_COUNT_1_BIT;

    VkPipelineColorBlendAttachmentState blendA{};
    blendA.blendEnable = VK_FALSE;
    blendA.colorWriteMask = VK_COLOR_COMPONENT_R_BIT | VK_COLOR_COMPONENT_G_BIT |
                            VK_COLOR_COMPONENT_B_BIT | VK_COLOR_COMPONENT_A_BIT;

    VkPipelineColorBlendStateCreateInfo blend{VK_STRUCTURE_TYPE_PIPELINE_COLOR_BLEND_STATE_CREATE_INFO};
    blend.attachmentCount = 1;
    blend.pAttachments = &blendA;

    VkGraphicsPipelineCreateInfo gpci{};
    gpci.sType = VK_STRUCTURE_TYPE_GRAPHICS_PIPELINE_CREATE_INFO;
    gpci.stageCount = 2;
    gpci.pStages = stages;
    gpci.pVertexInputState = &vi;
    gpci.pInputAssemblyState = &ia;
    gpci.pViewportState = &vs;
    gpci.pRasterizationState = &rs;
    gpci.pMultisampleState = &ms;
    gpci.pColorBlendState = &blend;
    gpci.pDynamicState = &dyn;
    gpci.layout = m_lutCombine.layout;
    gpci.renderPass = m_effectPass;

    bool ok = vkCreateGraphicsPipelines(m_device, VK_NULL_HANDLE, 1, &gpci, nullptr, &m_lutCombine.pipeline) == VK_SUCCESS;
    vkDestroyShaderModule(m_device, vert, nullptr);
    vkDestroyShaderModule(m_device, frag, nullptr);
    if (!ok) {
        vkDestroyPipelineLayout(m_device, m_lutCombine.layout, nullptr);
        m_lutCombine.layout = VK_NULL_HANDLE;
        return false;
    }
    return true;
}

const VC::VulkanWidget::LutResource* VC::VulkanWidget::getOrBuildLut(const std::string& filepath)
{
    auto it = m_lutCache.find(filepath);
    if (it != m_lutCache.end())
        return &it->second;

    cv::Mat atlas;
    int     N = 0;
    if (!parseCubeToAtlas(filepath, atlas, N)) {
        qWarning("LUT: failed to parse .cube '%s'", filepath.c_str());
        return nullptr;
    }

    // Reuse the same 2D-texture upload path Image/Video use (stores the
    // TextureResource in m_textures, freed in cleanup); we only need its
    // view+sampler for the 2-sampler LUT set.
    VkDescriptorSet ds = uploadTexture(atlas);
    const TextureResource& tex = m_textures[m_textureIndex[ds]];

    LutResource lr{tex.view, tex.sampler, N};
    auto [ins, _] = m_lutCache.emplace(filepath, lr);
    return &ins->second;
}

bool VC::VulkanWidget::ensureLutSetCapacity(size_t count)
{
    while (m_lutSets.size() < count) {
        VkDescriptorSet             set = VK_NULL_HANDLE;
        VkDescriptorSetAllocateInfo ai{VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO};
        ai.descriptorPool = m_lutPool;
        ai.descriptorSetCount = 1;
        ai.pSetLayouts = &m_lutLayout;
        if (vkAllocateDescriptorSets(m_device, &ai, &set) != VK_SUCCESS) return false;
        m_lutSets.push_back(set);
    }
    return true;
}

void VC::VulkanWidget::recordLutCombinePass(VkCommandBuffer cb, VkFramebuffer fb, VkDescriptorSet set, float intensity, float lutSize)
{
    VkClearValue clear = {{{0.f, 0.f, 0.f, 0.f}}};
    VkViewport   vp{0, 0, (float)m_swapExtent.width, (float)m_swapExtent.height, 0, 1};
    VkRect2D     sc{{0, 0}, m_swapExtent};

    VkRenderPassBeginInfo rpi{};
    rpi.sType = VK_STRUCTURE_TYPE_RENDER_PASS_BEGIN_INFO;
    rpi.renderPass = m_effectPass;
    rpi.framebuffer = fb;
    rpi.renderArea.extent = m_swapExtent;
    rpi.clearValueCount = 1;
    rpi.pClearValues = &clear;

    vkCmdBeginRenderPass(cb, &rpi, VK_SUBPASS_CONTENTS_INLINE);
    vkCmdSetViewport(cb, 0, 1, &vp);
    vkCmdSetScissor(cb, 0, 1, &sc);
    vkCmdBindPipeline(cb, VK_PIPELINE_BIND_POINT_GRAPHICS, m_lutCombine.pipeline);
    vkCmdBindDescriptorSets(cb, VK_PIPELINE_BIND_POINT_GRAPHICS, m_lutCombine.layout, 0, 1, &set, 0, nullptr);

    EffectPC pc{};
    pc.p[0] = intensity;
    pc.p[1] = lutSize;
    vkCmdPushConstants(cb, m_lutCombine.layout, VK_SHADER_STAGE_FRAGMENT_BIT, 0, sizeof(EffectPC), &pc);

    vkCmdDraw(cb, 6, 1, 0, 0);
    vkCmdEndRenderPass(cb);
}

void VC::VulkanWidget::recordGlowCombinePass(VkCommandBuffer cb, VkFramebuffer fb, VkDescriptorSet srcSet, float intensity)
{
    // No clear value: LOAD render pass preserves the original already in `fb`.
    VkViewport vp{0, 0, (float)m_swapExtent.width, (float)m_swapExtent.height, 0, 1};
    VkRect2D   sc{{0, 0}, m_swapExtent};

    VkRenderPassBeginInfo rpi{};
    rpi.sType = VK_STRUCTURE_TYPE_RENDER_PASS_BEGIN_INFO;
    rpi.renderPass = m_effectPassLoad;
    rpi.framebuffer = fb;
    rpi.renderArea.extent = m_swapExtent;
    rpi.clearValueCount = 0;
    rpi.pClearValues = nullptr;

    vkCmdBeginRenderPass(cb, &rpi, VK_SUBPASS_CONTENTS_INLINE);
    vkCmdSetViewport(cb, 0, 1, &vp);
    vkCmdSetScissor(cb, 0, 1, &sc);
    vkCmdBindPipeline(cb, VK_PIPELINE_BIND_POINT_GRAPHICS, m_glowCombine.pipeline);
    vkCmdBindDescriptorSets(cb, VK_PIPELINE_BIND_POINT_GRAPHICS, m_glowCombine.layout, 0, 1, &srcSet, 0, nullptr);

    EffectPC pc{};
    pc.p[0] = intensity;
    vkCmdPushConstants(cb, m_glowCombine.layout, VK_SHADER_STAGE_FRAGMENT_BIT, 0, sizeof(EffectPC), &pc);

    vkCmdDraw(cb, 6, 1, 0, 0);
    vkCmdEndRenderPass(cb);
}

void VC::VulkanWidget::recordEffectGeomPass(VkCommandBuffer cb, size_t meshIndex)
{
    VkClearValue clears[2] = {{{{0.f, 0.f, 0.f, 0.f}}}, {{{0.f, 0.f, 0.f, 0.f}}}};
    VkViewport   vp{0, 0, (float)m_swapExtent.width, (float)m_swapExtent.height, 0, 1};
    VkRect2D     sc{{0, 0}, m_swapExtent};

    VkRenderPassBeginInfo rpi{};
    rpi.sType = VK_STRUCTURE_TYPE_RENDER_PASS_BEGIN_INFO;
    rpi.renderPass = m_effectGeomPass;
    rpi.framebuffer = m_effectGeomFb;
    rpi.renderArea.extent = m_swapExtent;
    rpi.clearValueCount = 2;
    rpi.pClearValues = clears;

    vkCmdBeginRenderPass(cb, &rpi, VK_SUBPASS_CONTENTS_INLINE);
    vkCmdSetViewport(cb, 0, 1, &vp);
    vkCmdSetScissor(cb, 0, 1, &sc);

    // Use 1-sample geometry pipeline (m_effectPass is 1× sample)
    vkCmdBindPipeline(cb, VK_PIPELINE_BIND_POINT_GRAPHICS, m_effectGeomPipeline);
    vkCmdBindDescriptorSets(cb, VK_PIPELINE_BIND_POINT_GRAPHICS, m_pipelineLayout, 0, 1, &m_descriptorSet, 0, nullptr);

    VkDeviceSize zero = 0;
    vkCmdBindVertexBuffers(cb, 0, 1, &m_vertexBuffer, &zero);
    vkCmdBindIndexBuffer(cb, m_indexBuffer, 0, VK_INDEX_TYPE_UINT32);

    const Mesh&         mesh = m_meshes[meshIndex];
    const MeshDrawInfo& info = m_meshDrawInfos[meshIndex];
    if (mesh.hasTexture && mesh.textureDescriptor != VK_NULL_HANDLE) {
        vkCmdBindDescriptorSets(cb, VK_PIPELINE_BIND_POINT_GRAPHICS, m_pipelineLayout, 1, 1, &mesh.textureDescriptor, 0, nullptr);
    } else {
        vkCmdBindDescriptorSets(cb, VK_PIPELINE_BIND_POINT_GRAPHICS, m_pipelineLayout, 1, 1, &m_defaultTextureSet, 0, nullptr);
    }
    vkCmdDrawIndexed(cb, info.indexCount, 1, info.firstIndex, 0, 0);

    vkCmdEndRenderPass(cb);
}

void VC::VulkanWidget::recordEffectKernelPass(
    VkCommandBuffer cb, VkFramebuffer fb,
    VkDescriptorSet    srcSet,
    const std::string& name,
    float texelX, float texelY,
    const std::vector<float>& params
)
{
    std::string lower = name;
    std::transform(lower.begin(), lower.end(), lower.begin(), ::tolower);

    auto it = m_effectPipelines.find(lower);
    if (it == m_effectPipelines.end()) return;

    VkClearValue clear = {{{0.f, 0.f, 0.f, 0.f}}};
    VkViewport   vp{0, 0, (float)m_swapExtent.width, (float)m_swapExtent.height, 0, 1};
    VkRect2D     sc{{0, 0}, m_swapExtent};

    VkRenderPassBeginInfo rpi{};
    rpi.sType = VK_STRUCTURE_TYPE_RENDER_PASS_BEGIN_INFO;
    rpi.renderPass = m_effectPass;
    rpi.framebuffer = fb;
    rpi.renderArea.extent = m_swapExtent;
    rpi.clearValueCount = 1;
    rpi.pClearValues = &clear;

    vkCmdBeginRenderPass(cb, &rpi, VK_SUBPASS_CONTENTS_INLINE);
    vkCmdSetViewport(cb, 0, 1, &vp);
    vkCmdSetScissor(cb, 0, 1, &sc);
    vkCmdBindPipeline(cb, VK_PIPELINE_BIND_POINT_GRAPHICS, it->second.pipeline);
    vkCmdBindDescriptorSets(cb, VK_PIPELINE_BIND_POINT_GRAPHICS, it->second.layout, 0, 1, &srcSet, 0, nullptr);

    EffectPC pc{};
    pc.texelX = texelX;
    pc.texelY = texelY;
    for (size_t i = 0; i < std::min(params.size(), size_t(8)); i++)
        pc.p[i] = params[i];
    vkCmdPushConstants(cb, it->second.layout, VK_SHADER_STAGE_FRAGMENT_BIT, 0, sizeof(EffectPC), &pc);

    vkCmdDraw(cb, 6, 1, 0, 0);
    vkCmdEndRenderPass(cb);
}

// ============================================================================
// recordEffectPrepasses
//   Each effect-bearing mesh gets its own geometry pass + effect chain on the
//   shared ping/pong scratch images, finalized via the "Passthrough" shader
//   into its own dedicated result image (m_effectResults[slot]). These results
//   are composited in zIndex order by recordSceneDraws() below, instead of one
//   global post-process pass that ignores draw order.
// ============================================================================

void VC::VulkanWidget::recordEffectPrepasses(VkCommandBuffer cb)
{
    // Running index into m_lutSets across ALL lut combines this frame — a
    // descriptor set can't be re-pointed mid-command-buffer, so each combine
    // (any mesh, any lut effect) needs its own set.
    size_t lutN = 0;

    // effect-mesh position → result slot (shared with adjustment-layer flatten).
    std::unordered_map<size_t, size_t> effectSlotForMesh;
    for (size_t s = 0; s < m_effectMeshIndices.size(); ++s)
        effectSlotForMesh[m_effectMeshIndices[s]] = s;

    // Running index into m_adjustmentMeshPositions (ALs appear in slot order).
    size_t alIdx = 0;

    for (size_t slot = 0; slot < m_effectMeshIndices.size(); ++slot) {
        size_t meshIdx = m_effectMeshIndices[slot];

        if (m_meshes[meshIdx].isAdjustmentLayer) {
            // Seed ping with the flattened composite of everything below this
            // layer (see the headless renderer for the full walkthrough).
            size_t chunkBegin = (alIdx == 0) ? 0 : m_adjustmentMeshPositions[alIdx - 1] + 1;
            int    seedSlot   = (alIdx == 0) ? -1 : (int)effectSlotForMesh[m_adjustmentMeshPositions[alIdx - 1]];
            recordAdjustmentFlattenPass(cb, chunkBegin, meshIdx, seedSlot, effectSlotForMesh);
            ++alIdx;
        } else {
            recordEffectGeomPass(cb, meshIdx);
        }
        // RAW: flatten/geom's write of ping → first effect pass read of ping
        effectBarrier(cb, VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT, VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT, m_pingImage, VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT, VK_ACCESS_SHADER_READ_BIT);

        // Track which scratch image holds the current result instead of
        // forcing it back into ping after every effect — running single-pass
        // effects a second time just to land in ping doubled their GPU cost
        // and double-applied non-idempotent ones (gamma², 2× sweep intensity).
        bool inPing = true;

        for (const auto& eff : m_meshes[meshIdx].effects) {
            std::string lower = eff.name;
            std::transform(lower.begin(), lower.end(), lower.begin(), ::tolower);

            VkFramebuffer   srcFb = inPing ? m_pingFb : m_pongFb;
            VkFramebuffer   dstFb = inPing ? m_pongFb : m_pingFb;
            VkDescriptorSet srcSet = inPing ? m_pingSrcSet : m_pongSrcSet;
            VkDescriptorSet dstSet = inPing ? m_pongSrcSet : m_pingSrcSet;
            VkImage         srcImg = inPing ? m_pingImage : m_pongImage;
            VkImage         dstImg = inPing ? m_pongImage : m_pingImage;

            if (lower == "blur") {
                // Separable blur: H into dst, V back into src — result stays put.
                recordEffectKernelPass(cb, dstFb, srcSet, eff.name, 1.f / m_swapExtent.width, 0.f, eff.params);
                // RAW on dst + WAR on src (H wrote dst, read src; V reads dst, writes src)
                effectBarrier2(cb, dstImg, srcImg);

                recordEffectKernelPass(cb, srcFb, dstSet, eff.name, 0.f, 1.f / m_swapExtent.height, eff.params);
                // RAW: V's write of src → next pass read of src
                effectBarrier(cb, VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT, VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT, srcImg, VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT, VK_ACCESS_SHADER_READ_BIT);
            } else if (lower == "glow") {
                // Glow/bloom (Strategy B — additive combine). The ONE hand-built
                // exception to the single-sampler / CLEAR-blend effect-chain
                // convention: blur a copy of the input, additively composite the
                // halo back onto the sharp original. The original must survive
                // blur's in-place H/V passes, so stash it in the third buffer.
                // params arrive ALPHABETICALLY → [intensity, radius].
                float              intensity = eff.params.empty() ? 1.f : eff.params[0];
                std::vector<float> blurParams = {eff.params.size() > 1 ? eff.params[1] : 5.f};

                // P1: preserve the sharp original into the third buffer.
                recordEffectKernelPass(cb, m_thirdFb, srcSet, "Passthrough", 0.f, 0.f, {});
                effectBarrier(cb, VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT, VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT, m_thirdImage, VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT, VK_ACCESS_SHADER_READ_BIT);

                // P2/P3: blur src in place (identical topology to the blur branch).
                recordEffectKernelPass(cb, dstFb, srcSet, "Blur", 1.f / m_swapExtent.width, 0.f, blurParams);
                effectBarrier2(cb, dstImg, srcImg);
                recordEffectKernelPass(cb, srcFb, dstSet, "Blur", 0.f, 1.f / m_swapExtent.height, blurParams);
                effectBarrier(cb, VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT, VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT, srcImg, VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT, VK_ACCESS_SHADER_READ_BIT);
                // Now: src = blurred, third = original, dst = stale (last read by P3).

                // P4: lay a fresh copy of the original into dst as the combine base.
                // WAR: P3 sampled dst — that read must finish before P4 clears+writes it.
                effectBarrier(cb, VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT, VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT, dstImg, VK_ACCESS_SHADER_READ_BIT, VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT);
                recordEffectKernelPass(cb, dstFb, m_thirdSrcSet, "Passthrough", 0.f, 0.f, {});
                // P4's colour write must be visible to P5's LOAD (read+write of dst).
                effectBarrier(cb, VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT, VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT, dstImg, VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT, VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT | VK_ACCESS_COLOR_ATTACHMENT_READ_BIT);

                // P5: additive combine. LOAD keeps dst's original; the (ONE,ONE)
                // blend adds intensity*blurred (sampled from src) on top.
                recordGlowCombinePass(cb, dstFb, srcSet, intensity);
                // Result now lives in dst — flip, same convention as the else branch.
                effectBarrier2(cb, dstImg, srcImg);
                inPing = !inPing;
            } else if (lower == "lut") {
                // LUT color grade — the THIRD hand-built exception (glow, matte
                // first). It samples a SECOND texture: a .cube atlas built ONCE
                // from eff.strParam (the file path) and cached across every
                // frame/mesh in m_lutCache. intensity is the only numeric arg
                // (p[0]); the atlas size rides separately.
                const LutResource* lr = eff.strParam.empty() ? nullptr : getOrBuildLut(eff.strParam);
                if (lr) {
                    float       intensity = eff.params.empty() ? 1.f : eff.params[0];
                    VkImageView srcView = inPing ? m_pingView : m_pongView;

                    VkDescriptorSet       lutSet = m_lutSets[lutN++];
                    VkDescriptorImageInfo infos[2] = {
                        {m_effectSampler, srcView, VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL},
                        {lr->sampler, lr->view, VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL},
                    };
                    VkWriteDescriptorSet w[2]{};
                    for (int b = 0; b < 2; ++b) {
                        w[b].sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
                        w[b].dstSet = lutSet;
                        w[b].dstBinding = b;
                        w[b].descriptorCount = 1;
                        w[b].descriptorType = VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER;
                        w[b].pImageInfo = &infos[b];
                    }
                    vkUpdateDescriptorSets(m_device, 2, w, 0, nullptr);

                    recordLutCombinePass(cb, dstFb, lutSet, intensity, (float)lr->size);
                    effectBarrier2(cb, dstImg, srcImg);
                    inPing = !inPing;
                }
                // LUT failed to load → skip silently, layer stays ungraded.
            } else if (lower == "mathshader") {
                // Generic runtime-loaded "math shader" (fragcoord.xyz ports —
                // silk is a bundled preset of this): eff.strParam carries the
                // GLSL file path (the same strParam channel LUT uses for its
                // .cube path). The pipeline is compiled once per file and then
                // recorded exactly like any auto-discovered effect pass.
                if (!eff.strParam.empty() && ensureMathPipeline(eff.strParam)) {
                    recordEffectKernelPass(cb, dstFb, srcSet, mathPipelineKey(eff.strParam),
                                           1.f / m_swapExtent.width, 1.f / m_swapExtent.height, eff.params);
                    effectBarrier2(cb, dstImg, srcImg);
                    inPing = !inPing;
                }
                // missing/broken file → logged once by ensureMathPipeline,
                // layer passes through unmodified.
            } else {
                // Single pass: src → dst, result moves to dst. texelX/texelY
                // carry the real texel size here (Blur repurposes them as its
                // per-pass step direction above) — effects like Pixelate need
                // them to convert screen-pixel params into UV space.
                recordEffectKernelPass(cb, dstFb, srcSet, eff.name, 1.f / m_swapExtent.width, 1.f / m_swapExtent.height, eff.params);
                // RAW on dst (next pass reads it) + WAR on src (next pass may write it)
                effectBarrier2(cb, dstImg, srcImg);
                inPing = !inPing;
            }
        }

        // Flush the final result into this mesh's dedicated result image.
        recordEffectKernelPass(cb, m_effectResults[slot].framebuffer, inPing ? m_pingSrcSet : m_pongSrcSet, "Passthrough", 0.f, 0.f, {});
        effectBarrier(cb, VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT, VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT, m_effectResults[slot].image, VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT, VK_ACCESS_SHADER_READ_BIT);
    }

    // ── Matte combine phase — mirrors the headless renderer. Every consumer AND
    // source slot is populated by Phase 1 above; here each consumer samples its
    // own slot (content) + its source's slot (matte) into ping, then Passthrough
    // ping back into the consumer's slot (masked result the main pass draws). ──
    {
        std::unordered_map<size_t, size_t> meshPosToSlot;
        for (size_t s = 0; s < m_effectMeshIndices.size(); ++s)
            meshPosToSlot[m_effectMeshIndices[s]] = s;

        size_t matteN = 0;
        for (size_t s = 0; s < m_effectMeshIndices.size(); ++s) {
            size_t      consumerPos = m_effectMeshIndices[s];
            const Mesh& mesh = m_meshes[consumerPos];
            if (mesh.matteSourceInputIndex < 0) continue;

            auto srcMeshIt = m_inputIndexToMeshPos.find(mesh.matteSourceInputIndex);
            if (srcMeshIt == m_inputIndexToMeshPos.end()) continue; // source absent → leave unmasked
            auto srcSlotIt = meshPosToSlot.find(srcMeshIt->second);
            if (srcSlotIt == meshPosToSlot.end()) continue;

            const EffectResultSlot& consumerSlot = m_effectResults[s];
            const EffectResultSlot& sourceSlot = m_effectResults[srcSlotIt->second];

            VkDescriptorSet matteSet = m_matteSets[matteN++];
            VkDescriptorImageInfo infos[2] = {
                {m_effectSampler, consumerSlot.view, VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL},
                {m_effectSampler, sourceSlot.view, VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL},
            };
            VkWriteDescriptorSet w[2]{};
            for (int b = 0; b < 2; ++b) {
                w[b].sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
                w[b].dstSet = matteSet;
                w[b].dstBinding = b;
                w[b].descriptorCount = 1;
                w[b].descriptorType = VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER;
                w[b].pImageInfo = &infos[b];
            }
            vkUpdateDescriptorSets(m_device, 2, w, 0, nullptr);

            // WAR: prior read of ping finishes before the combine clears+writes it.
            effectBarrier(cb, VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT, VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT, m_pingImage, VK_ACCESS_SHADER_READ_BIT, VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT);
            recordMatteCombinePass(cb, m_pingFb, matteSet);
            // RAW on ping (Passthrough reads it) + WAR on consumer slot (combine read → Passthrough write).
            effectBarrier2(cb, m_pingImage, consumerSlot.image);

            recordEffectKernelPass(cb, consumerSlot.framebuffer, m_pingSrcSet, "Passthrough", 0.f, 0.f, {});
            effectBarrier(cb, VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT, VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT, consumerSlot.image, VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT, VK_ACCESS_SHADER_READ_BIT);
        }
    }
}

// ============================================================================
// recordSceneDraws
//   m_meshes is already zIndex/zOrderSeq-sorted (Core::generateMeshes), so a
//   single ordered pass — interleaving normal-mesh geometry with effect-mesh
//   composite quads — preserves correct draw order for both.
// ============================================================================

void VC::VulkanWidget::recordSceneDraws(VkCommandBuffer cb)
{
    std::unordered_map<size_t, size_t> effectSlotForMesh;
    for (size_t s = 0; s < m_effectMeshIndices.size(); ++s)
        effectSlotForMesh[m_effectMeshIndices[s]] = s;

    // With adjustment layers present, everything at/below the topmost layer is
    // already baked+graded into its result: composite it as one fullscreen quad,
    // then draw only the meshes ABOVE it. No adjustment layers → drawStart = 0,
    // no seed quad, byte-identical to before.
    size_t drawStart = 0;
    if (!m_adjustmentMeshPositions.empty()) {
        size_t lastAL = m_adjustmentMeshPositions.back();
        auto   it = effectSlotForMesh.find(lastAL);
        if (it != effectSlotForMesh.end())
            recordCompositeResultQuad(cb, m_pipelines[0], m_effectResults[it->second].descriptorSet);
        drawStart = lastAL + 1;
    }
    recordMeshRange(cb, drawStart, m_meshes.size(), effectSlotForMesh, m_pipelines);
}

// ── Adjustment-layer support (mirrors the headless renderer; see it for the
// full walkthrough). The one structural divergence is the pipeline array the
// flatten passes bind: m_effectBlendPipelines[] (1-sample), NOT m_pipelines[]
// (4× MSAA), because the widget's main pass is MSAA+resolve while the flatten
// target (ping) is 1-sample. ─────────────────────────────────────────────────

void VC::VulkanWidget::recordMeshRange(
    VkCommandBuffer cb, size_t begin, size_t end,
    const std::unordered_map<size_t, size_t>& effectSlotForMesh,
    const VkPipeline* pipelines
)
{
    VkBuffer     vbufs[] = {m_vertexBuffer};
    VkDeviceSize offsets[] = {0};
    VkDeviceSize zero = 0;

    int boundBlend = -1;
    for (size_t mi = begin; mi < end; ++mi) {
        const Mesh& mesh = m_meshes[mi];

        // Matte sources are consumed only as a mask; adjustment layers never draw
        // their own geometry (their grade reaches the screen via a result quad).
        if (m_matteSourceMeshPositions.count(mi) || mesh.isAdjustmentLayer)
            continue;

        auto effIt = effectSlotForMesh.find(mi);

        int bm = mesh.blendMode;
        if (bm < 0 || bm >= kBlendModeCount) bm = 0;
        if (bm != boundBlend) {
            boundBlend = bm;
            vkCmdBindPipeline(cb, VK_PIPELINE_BIND_POINT_GRAPHICS, pipelines[bm]);
        }

        if (effIt == effectSlotForMesh.end()) {
            const MeshDrawInfo& info = m_meshDrawInfos[mi];
            vkCmdBindVertexBuffers(cb, 0, 1, vbufs, offsets);
            vkCmdBindIndexBuffer(cb, m_indexBuffer, 0, VK_INDEX_TYPE_UINT32);
            if (mesh.hasTexture && mesh.textureDescriptor != VK_NULL_HANDLE)
                vkCmdBindDescriptorSets(cb, VK_PIPELINE_BIND_POINT_GRAPHICS, m_pipelineLayout, 1, 1, &mesh.textureDescriptor, 0, nullptr);
            else
                vkCmdBindDescriptorSets(cb, VK_PIPELINE_BIND_POINT_GRAPHICS, m_pipelineLayout, 1, 1, &m_defaultTextureSet, 0, nullptr);
            vkCmdDrawIndexed(cb, info.indexCount, 1, info.firstIndex, 0, 0);
        } else {
            // Composite this mesh's effect result as a full-resolution textured quad.
            vkCmdBindVertexBuffers(cb, 0, 1, &m_compVtxBuf, &zero);
            vkCmdBindIndexBuffer(cb, m_compIdxBuf, 0, VK_INDEX_TYPE_UINT32);
            vkCmdBindDescriptorSets(cb, VK_PIPELINE_BIND_POINT_GRAPHICS, m_pipelineLayout, 1, 1, &m_effectResults[effIt->second].descriptorSet, 0, nullptr);
            vkCmdDrawIndexed(cb, 6, 1, 0, 0, 0);
        }
    }
}

void VC::VulkanWidget::recordCompositeResultQuad(VkCommandBuffer cb, VkPipeline pipeline, VkDescriptorSet resultSet)
{
    VkDeviceSize zero = 0;
    vkCmdBindPipeline(cb, VK_PIPELINE_BIND_POINT_GRAPHICS, pipeline);
    vkCmdBindVertexBuffers(cb, 0, 1, &m_compVtxBuf, &zero);
    vkCmdBindIndexBuffer(cb, m_compIdxBuf, 0, VK_INDEX_TYPE_UINT32);
    vkCmdBindDescriptorSets(cb, VK_PIPELINE_BIND_POINT_GRAPHICS, m_pipelineLayout, 1, 1, &resultSet, 0, nullptr);
    vkCmdDrawIndexed(cb, 6, 1, 0, 0, 0);
}

void VC::VulkanWidget::recordAdjustmentFlattenPass(
    VkCommandBuffer cb, size_t begin, size_t end, int seedSlot,
    const std::unordered_map<size_t, size_t>& effectSlotForMesh
)
{
    // 1-sample CLEAR into ping via m_effectPass (same target the kernel passes
    // write) — no MSAA here, matching the headless renderer's non-supersampled
    // flatten. Transparent clear preserves the composite's own alpha.
    VkClearValue clear = {{{0.f, 0.f, 0.f, 0.f}}};
    VkViewport   vp{0, 0, (float)m_swapExtent.width, (float)m_swapExtent.height, 0, 1};
    VkRect2D     sc{{0, 0}, m_swapExtent};

    VkRenderPassBeginInfo rpi{};
    rpi.sType = VK_STRUCTURE_TYPE_RENDER_PASS_BEGIN_INFO;
    rpi.renderPass = m_effectPass;
    rpi.framebuffer = m_pingFb;
    rpi.renderArea.extent = m_swapExtent;
    rpi.clearValueCount = 1;
    rpi.pClearValues = &clear;

    vkCmdBeginRenderPass(cb, &rpi, VK_SUBPASS_CONTENTS_INLINE);
    vkCmdSetViewport(cb, 0, 1, &vp);
    vkCmdSetScissor(cb, 0, 1, &sc);
    // set=0 (UBO) shared across every blend pipeline via m_pipelineLayout.
    vkCmdBindDescriptorSets(cb, VK_PIPELINE_BIND_POINT_GRAPHICS, m_pipelineLayout, 0, 1, &m_descriptorSet, 0, nullptr);

    // Seed with the previous adjustment layer's graded result (Normal blend over
    // the transparent clear makes it the base). Both the seed and the chunk
    // meshes use the 1-sample blend array — see the array's decl for why.
    if (seedSlot >= 0)
        recordCompositeResultQuad(cb, m_effectBlendPipelines[0], m_effectResults[seedSlot].descriptorSet);

    recordMeshRange(cb, begin, end, effectSlotForMesh, m_effectBlendPipelines);

    vkCmdEndRenderPass(cb);
}

// ============================================================================
// cleanup — destructor helper
//   Destroys every Vulkan object in reverse-creation order.
// ============================================================================

void VC::VulkanWidget::cleanup()
{
    if (!m_device) {
        return;
    }
    vkDeviceWaitIdle(m_device);

    vkDestroySemaphore(m_device, m_imageAvailableSemaphore, nullptr);
    vkDestroySemaphore(m_device, m_renderFinishedSemaphore, nullptr);
    vkDestroyFence(m_device, m_inFlightFence, nullptr);

    vkDestroyCommandPool(m_device, m_commandPool, nullptr); // frees command buffers implicitly

    for (auto fb : m_framebuffers) {
        vkDestroyFramebuffer(m_device, fb, nullptr);
    }

    destroySsaaResources();
    destroyReadbackResources();

    for (VkPipeline& p : m_pipelines) {
        if (p != VK_NULL_HANDLE) vkDestroyPipeline(m_device, p, nullptr);
    }
    if (m_effectGeomPipeline) vkDestroyPipeline(m_device, m_effectGeomPipeline, nullptr);
    for (VkPipeline& p : m_effectBlendPipelines) {
        if (p != VK_NULL_HANDLE) vkDestroyPipeline(m_device, p, nullptr);
    }
    for (auto& [name, ep] : m_effectPipelines) {
        vkDestroyPipeline(m_device, ep.pipeline, nullptr);
        vkDestroyPipelineLayout(m_device, ep.layout, nullptr);
    }
    vkDestroyPipelineLayout(m_device, m_pipelineLayout, nullptr);

    // Glow-only extras
    if (m_glowCombine.pipeline) vkDestroyPipeline(m_device, m_glowCombine.pipeline, nullptr);
    if (m_glowCombine.layout) vkDestroyPipelineLayout(m_device, m_glowCombine.layout, nullptr);
    // Matte-only extras (sets freed with the pool)
    if (m_matteCombine.pipeline) vkDestroyPipeline(m_device, m_matteCombine.pipeline, nullptr);
    if (m_matteCombine.layout) vkDestroyPipelineLayout(m_device, m_matteCombine.layout, nullptr);
    if (m_mattePool) vkDestroyDescriptorPool(m_device, m_mattePool, nullptr);
    if (m_matteLayout) vkDestroyDescriptorSetLayout(m_device, m_matteLayout, nullptr);
    // LUT-only extras (sets freed with the pool; atlas images live in
    // m_textures, freed in the m_textures loop below).
    if (m_lutCombine.pipeline) vkDestroyPipeline(m_device, m_lutCombine.pipeline, nullptr);
    if (m_lutCombine.layout) vkDestroyPipelineLayout(m_device, m_lutCombine.layout, nullptr);
    if (m_lutPool) vkDestroyDescriptorPool(m_device, m_lutPool, nullptr);
    if (m_lutLayout) vkDestroyDescriptorSetLayout(m_device, m_lutLayout, nullptr);
    if (m_effectPassLoad) vkDestroyRenderPass(m_device, m_effectPassLoad, nullptr);
    if (m_thirdFb) vkDestroyFramebuffer(m_device, m_thirdFb, nullptr);
    if (m_thirdView) vkDestroyImageView(m_device, m_thirdView, nullptr);
    if (m_thirdImage) vkDestroyImage(m_device, m_thirdImage, nullptr);
    if (m_thirdMemory) vkFreeMemory(m_device, m_thirdMemory, nullptr);

    if (m_effectSampler) vkDestroySampler(m_device, m_effectSampler, nullptr);
    if (m_effectPass) vkDestroyRenderPass(m_device, m_effectPass, nullptr);
    if (m_effectGeomPass) vkDestroyRenderPass(m_device, m_effectGeomPass, nullptr);
    if (m_effectGeomFb) vkDestroyFramebuffer(m_device, m_effectGeomFb, nullptr);
    if (m_pingFb) vkDestroyFramebuffer(m_device, m_pingFb, nullptr);
    if (m_pongFb) vkDestroyFramebuffer(m_device, m_pongFb, nullptr);
    if (m_effectMsaaView) vkDestroyImageView(m_device, m_effectMsaaView, nullptr);
    if (m_effectMsaaImage) vkDestroyImage(m_device, m_effectMsaaImage, nullptr);
    if (m_effectMsaaMemory) vkFreeMemory(m_device, m_effectMsaaMemory, nullptr);
    if (m_pingView) vkDestroyImageView(m_device, m_pingView, nullptr);
    if (m_pingImage) vkDestroyImage(m_device, m_pingImage, nullptr);
    if (m_pingMemory) vkFreeMemory(m_device, m_pingMemory, nullptr);
    if (m_pongView) vkDestroyImageView(m_device, m_pongView, nullptr);
    if (m_pongImage) vkDestroyImage(m_device, m_pongImage, nullptr);
    if (m_pongMemory) vkFreeMemory(m_device, m_pongMemory, nullptr);
    if (m_compVtxBuf) vkDestroyBuffer(m_device, m_compVtxBuf, nullptr);
    if (m_compVtxMem) vkFreeMemory(m_device, m_compVtxMem, nullptr);
    if (m_compIdxBuf) vkDestroyBuffer(m_device, m_compIdxBuf, nullptr);
    if (m_compIdxMem) vkFreeMemory(m_device, m_compIdxMem, nullptr);

    // Destroy per-mesh uploaded textures
    for (auto& tex : m_textures) {
        vkDestroySampler(m_device, tex.sampler, nullptr);
        vkDestroyImageView(m_device, tex.view, nullptr);
        vkDestroyImage(m_device, tex.image, nullptr);
        vkFreeMemory(m_device, tex.memory, nullptr);
    }
    m_textures.clear();

    // Destroy default 1×1 white texture
    vkDestroySampler(m_device, m_defaultTexture.sampler, nullptr);
    vkDestroyImageView(m_device, m_defaultTexture.view, nullptr);
    vkDestroyImage(m_device, m_defaultTexture.image, nullptr);
    vkFreeMemory(m_device, m_defaultTexture.memory, nullptr);

    vkDestroyDescriptorPool(m_device, m_texturePool, nullptr); // frees texture sets implicitly
    vkDestroyDescriptorSetLayout(m_device, m_textureSetLayout, nullptr);

    vkDestroyDescriptorPool(m_device, m_descriptorPool, nullptr); // frees UBO set implicitly
    vkDestroyDescriptorSetLayout(m_device, m_descriptorSetLayout, nullptr);

    vkDestroyRenderPass(m_device, m_renderPass, nullptr);

    for (auto iv : m_swapImageViews) {
        vkDestroyImageView(m_device, iv, nullptr);
    }
    vkDestroySwapchainKHR(m_device, m_swapchain, nullptr);
    // VkImages owned by the swapchain are freed with it — do not destroy manually.

    vkDestroyBuffer(m_device, m_vertexBuffer, nullptr);
    vkFreeMemory(m_device, m_vertexMemory, nullptr);
    vkDestroyBuffer(m_device, m_indexBuffer, nullptr);
    vkFreeMemory(m_device, m_indexMemory, nullptr);
    vkDestroyBuffer(m_device, m_uniformBuffer, nullptr);
    vkFreeMemory(m_device, m_uniformMemory, nullptr);

    vkDestroySurfaceKHR(m_instance, m_surface, nullptr);
    vkDestroyDevice(m_device, nullptr);
    vkDestroyInstance(m_instance, nullptr);
}
