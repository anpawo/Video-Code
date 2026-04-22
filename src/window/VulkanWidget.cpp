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

#include <vulkan/vulkan_metal.h>

#include <QDebug>
#include <QResizeEvent>
#include <QWindow>
#include <chrono>
#include <cstring>

#include <fstream>
#include <sstream>

#include "vulkan/MetalSurface.hpp"   // CAMetalLayer bridge (macOS only)
#include "vulkan/ShaderCompiler.hpp" // Runtime GLSL → SPIR-V via glslang

// ============================================================================
// loadShaderSource
//   Reads a GLSL file from assets/shaders/quadraticBezier/ at runtime.
// ============================================================================

static std::string loadShaderSource(const std::string& filename)
{
    std::string path = std::string(SHADER_DIR) + "/quadraticBezier/" + filename;
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

    for (const auto& mesh : meshes) {
        MeshDrawInfo info{};
        info.firstIndex = static_cast<uint32_t>(m_indices.size());
        info.indexCount = static_cast<uint32_t>(mesh.indices.size());

        uint16_t vertexOffset = static_cast<uint16_t>(m_vertices.size());
        m_vertices.insert(m_vertices.end(), mesh.vertices.begin(), mesh.vertices.end());
        for (auto idx : mesh.indices) {
            m_indices.push_back(vertexOffset + idx);
        }
        m_meshDrawInfos.push_back(info);
    }
    m_geomDirty = true;
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
    // Attach a CAMetalLayer to the Qt native window (macOS).
    WId handle = winId();
    m_metalLayer = createMetalLayer(reinterpret_cast<void*>(handle));

    if (!createInstance()) {
        qWarning("createInstance failed");
        return false;
    }
    if (!createSurface()) {
        qWarning("createSurface failed");
        return false;
    }
    if (!pickPhysicalDevice()) {
        qWarning("pickPhysicalDevice failed");
        return false;
    }
    if (!createDevice()) {
        qWarning("createDevice failed");
        return false;
    }
    if (!createSwapchain()) {
        qWarning("createSwapchain failed");
        return false;
    }
    if (!createSsaaResources()) {
        qWarning("createSsaaResources failed");
        return false;
    }
    if (!createReadbackResources()) {
        qWarning("createReadbackResources failed");
        return false;
    }
    if (!createRenderPass()) {
        qWarning("createRenderPass failed");
        return false;
    }
    if (!createUniformBuffer()) {
        qWarning("createUniformBuffer failed");
        return false;
    }
    if (!createDescriptorSet()) {
        qWarning("createDescriptorSet failed");
        return false;
    }
    if (!createPipeline()) {
        qWarning("createPipeline failed");
        return false;
    }
    if (!createVertexBuffer()) {
        qWarning("createVertexBuffer failed");
        return false;
    }
    if (!createIndexBuffer()) {
        qWarning("createIndexBuffer failed");
        return false;
    }
    if (!createFramebuffers()) {
        qWarning("createFramebuffers failed");
        return false;
    }
    if (!createCommandPool()) {
        qWarning("createCommandPool failed");
        return false;
    }

    // Upload the default 1×1 white texture now that the command pool exists.
    cv::Mat white(1, 1, CV_8UC4, cv::Scalar(255, 255, 255, 255));
    m_defaultTextureSet = uploadTexture(white);
    if (m_defaultTextureSet == VK_NULL_HANDLE) {
        qWarning("default texture upload failed");
        return false;
    }

    if (!createCommandBuffers()) {
        qWarning("createCommandBuffers failed");
        return false;
    }
    if (!createSyncObjects()) {
        qWarning("createSyncObjects failed");
        return false;
    }

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
        VK_EXT_METAL_SURFACE_EXTENSION_NAME,
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
//   Delegates to metal_surface.mm which calls vkCreateMetalSurfaceEXT.
// ============================================================================

bool VC::VulkanWidget::createSurface()
{
    m_surface = createMetalSurface(m_instance, m_metalLayer);
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
//   VK_KHR_portability_subset is required by MoltenVK on macOS.
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
        "VK_KHR_portability_subset",
    };

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
    m_swapFormat = formats[0].format;

    VkSwapchainCreateInfoKHR ci{};
    ci.sType = VK_STRUCTURE_TYPE_SWAPCHAIN_CREATE_INFO_KHR;
    ci.surface = m_surface;
    ci.minImageCount = 2;
    ci.imageFormat = m_swapFormat;
    ci.imageColorSpace = formats[0].colorSpace;
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
        ici.sType         = VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO;
        ici.imageType     = VK_IMAGE_TYPE_2D;
        ici.format        = m_swapFormat;
        ici.extent        = {m_swapExtent.width, m_swapExtent.height, 1};
        ici.mipLevels     = 1;
        ici.arrayLayers   = 1;
        ici.samples       = VK_SAMPLE_COUNT_4_BIT;
        ici.tiling        = VK_IMAGE_TILING_OPTIMAL;
        ici.usage         = VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT;
        ici.sharingMode   = VK_SHARING_MODE_EXCLUSIVE;
        ici.initialLayout = VK_IMAGE_LAYOUT_UNDEFINED;

        if (vkCreateImage(m_device, &ici, nullptr, &m_ssaaImage) != VK_SUCCESS)
            return false;

        VkMemoryRequirements memReq;
        vkGetImageMemoryRequirements(m_device, m_ssaaImage, &memReq);

        VkMemoryAllocateInfo ai{};
        ai.sType           = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
        ai.allocationSize  = memReq.size;
        ai.memoryTypeIndex = findMemoryType(memReq.memoryTypeBits, VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT);

        if (vkAllocateMemory(m_device, &ai, nullptr, &m_ssaaMemory) != VK_SUCCESS)
            return false;
        vkBindImageMemory(m_device, m_ssaaImage, m_ssaaMemory, 0);

        VkImageViewCreateInfo ivci{};
        ivci.sType            = VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO;
        ivci.image            = m_ssaaImage;
        ivci.viewType         = VK_IMAGE_VIEW_TYPE_2D;
        ivci.format           = m_swapFormat;
        ivci.subresourceRange = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1};

        if (vkCreateImageView(m_device, &ivci, nullptr, &m_ssaaImageView) != VK_SUCCESS)
            return false;
    }

    // ── Resolve image (1 sample, TRANSFER_SRC for readFrame) ─────────────
    {
        VkImageCreateInfo ici{};
        ici.sType         = VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO;
        ici.imageType     = VK_IMAGE_TYPE_2D;
        ici.format        = m_swapFormat;
        ici.extent        = {m_swapExtent.width, m_swapExtent.height, 1};
        ici.mipLevels     = 1;
        ici.arrayLayers   = 1;
        ici.samples       = VK_SAMPLE_COUNT_1_BIT;
        ici.tiling        = VK_IMAGE_TILING_OPTIMAL;
        ici.usage         = VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT | VK_IMAGE_USAGE_TRANSFER_SRC_BIT;
        ici.sharingMode   = VK_SHARING_MODE_EXCLUSIVE;
        ici.initialLayout = VK_IMAGE_LAYOUT_UNDEFINED;

        if (vkCreateImage(m_device, &ici, nullptr, &m_resolveImage) != VK_SUCCESS)
            return false;

        VkMemoryRequirements memReq;
        vkGetImageMemoryRequirements(m_device, m_resolveImage, &memReq);

        VkMemoryAllocateInfo ai{};
        ai.sType           = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
        ai.allocationSize  = memReq.size;
        ai.memoryTypeIndex = findMemoryType(memReq.memoryTypeBits, VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT);

        if (vkAllocateMemory(m_device, &ai, nullptr, &m_resolveMemory) != VK_SUCCESS)
            return false;
        vkBindImageMemory(m_device, m_resolveImage, m_resolveMemory, 0);

        VkImageViewCreateInfo ivci{};
        ivci.sType            = VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO;
        ivci.image            = m_resolveImage;
        ivci.viewType         = VK_IMAGE_VIEW_TYPE_2D;
        ivci.format           = m_swapFormat;
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
    ici.sType         = VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO;
    ici.imageType     = VK_IMAGE_TYPE_2D;
    ici.format        = VK_FORMAT_B8G8R8A8_UNORM; // matches OpenCV BGRA layout
    ici.extent        = {m_swapExtent.width, m_swapExtent.height, 1};
    ici.mipLevels     = 1;
    ici.arrayLayers   = 1;
    ici.samples       = VK_SAMPLE_COUNT_1_BIT;
    ici.tiling        = VK_IMAGE_TILING_LINEAR;
    ici.usage         = VK_IMAGE_USAGE_TRANSFER_DST_BIT;
    ici.sharingMode   = VK_SHARING_MODE_EXCLUSIVE;
    ici.initialLayout = VK_IMAGE_LAYOUT_UNDEFINED;

    if (vkCreateImage(m_device, &ici, nullptr, &m_readbackImage) != VK_SUCCESS) {
        return false;
    }

    VkMemoryRequirements memReq;
    vkGetImageMemoryRequirements(m_device, m_readbackImage, &memReq);

    VkMemoryAllocateInfo ai{};
    ai.sType           = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
    ai.allocationSize  = memReq.size;
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
    msaaAttachment.format         = m_swapFormat;
    msaaAttachment.samples        = VK_SAMPLE_COUNT_4_BIT;
    msaaAttachment.loadOp         = VK_ATTACHMENT_LOAD_OP_CLEAR;
    msaaAttachment.storeOp        = VK_ATTACHMENT_STORE_OP_DONT_CARE;
    msaaAttachment.stencilLoadOp  = VK_ATTACHMENT_LOAD_OP_DONT_CARE;
    msaaAttachment.stencilStoreOp = VK_ATTACHMENT_STORE_OP_DONT_CARE;
    msaaAttachment.initialLayout  = VK_IMAGE_LAYOUT_UNDEFINED;
    msaaAttachment.finalLayout    = VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL;

    // Attachment 1: Resolve target — render pass writes resolved pixels here.
    // finalLayout = TRANSFER_SRC_OPTIMAL so readFrame can blit straight from it;
    // for live rendering we add one barrier after the pass to go to PRESENT_SRC_KHR.
    VkAttachmentDescription resolveAttachment{};
    resolveAttachment.format         = m_swapFormat;
    resolveAttachment.samples        = VK_SAMPLE_COUNT_1_BIT;
    resolveAttachment.loadOp         = VK_ATTACHMENT_LOAD_OP_DONT_CARE;
    resolveAttachment.storeOp        = VK_ATTACHMENT_STORE_OP_STORE;
    resolveAttachment.stencilLoadOp  = VK_ATTACHMENT_LOAD_OP_DONT_CARE;
    resolveAttachment.stencilStoreOp = VK_ATTACHMENT_STORE_OP_DONT_CARE;
    resolveAttachment.initialLayout  = VK_IMAGE_LAYOUT_UNDEFINED;
    resolveAttachment.finalLayout    = VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL;

    VkAttachmentReference colorRef{};
    colorRef.attachment = 0;
    colorRef.layout     = VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL;

    VkAttachmentReference resolveRef{};
    resolveRef.attachment = 1;
    resolveRef.layout     = VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL;

    VkSubpassDescription subpass{};
    subpass.pipelineBindPoint    = VK_PIPELINE_BIND_POINT_GRAPHICS;
    subpass.colorAttachmentCount = 1;
    subpass.pColorAttachments    = &colorRef;
    subpass.pResolveAttachments  = &resolveRef;

    VkSubpassDependency deps[2]{};
    deps[0].srcSubpass    = VK_SUBPASS_EXTERNAL;
    deps[0].dstSubpass    = 0;
    deps[0].srcStageMask  = VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT;
    deps[0].dstStageMask  = VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT;
    deps[0].dstAccessMask = VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT;

    // Ensure resolve is visible to TRANSFER ops that follow (readFrame blit).
    deps[1].srcSubpass    = 0;
    deps[1].dstSubpass    = VK_SUBPASS_EXTERNAL;
    deps[1].srcStageMask  = VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT;
    deps[1].srcAccessMask = VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT;
    deps[1].dstStageMask  = VK_PIPELINE_STAGE_TRANSFER_BIT;
    deps[1].dstAccessMask = VK_ACCESS_TRANSFER_READ_BIT;

    VkAttachmentDescription attachments[2] = {msaaAttachment, resolveAttachment};

    VkRenderPassCreateInfo ci{};
    ci.sType           = VK_STRUCTURE_TYPE_RENDER_PASS_CREATE_INFO;
    ci.attachmentCount = 2;
    ci.pAttachments    = attachments;
    ci.subpassCount    = 1;
    ci.pSubpasses      = &subpass;
    ci.dependencyCount = 2;
    ci.pDependencies   = deps;

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
    uboBinding.binding         = 0;
    uboBinding.descriptorType  = VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER;
    uboBinding.descriptorCount = 1;
    uboBinding.stageFlags      = VK_SHADER_STAGE_FRAGMENT_BIT;

    VkDescriptorSetLayoutCreateInfo uboLci{};
    uboLci.sType        = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO;
    uboLci.bindingCount = 1;
    uboLci.pBindings    = &uboBinding;
    vkCreateDescriptorSetLayout(m_device, &uboLci, nullptr, &m_descriptorSetLayout);

    VkDescriptorPoolSize uboPs{};
    uboPs.type            = VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER;
    uboPs.descriptorCount = 1;

    VkDescriptorPoolCreateInfo uboPci{};
    uboPci.sType         = VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO;
    uboPci.poolSizeCount = 1;
    uboPci.pPoolSizes    = &uboPs;
    uboPci.maxSets       = 1;
    vkCreateDescriptorPool(m_device, &uboPci, nullptr, &m_descriptorPool);

    VkDescriptorSetAllocateInfo uboAi{};
    uboAi.sType              = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO;
    uboAi.descriptorPool     = m_descriptorPool;
    uboAi.descriptorSetCount = 1;
    uboAi.pSetLayouts        = &m_descriptorSetLayout;
    vkAllocateDescriptorSets(m_device, &uboAi, &m_descriptorSet);

    VkDescriptorBufferInfo bufInfo{};
    bufInfo.buffer = m_uniformBuffer;
    bufInfo.offset = 0;
    bufInfo.range  = sizeof(UniformData);

    VkWriteDescriptorSet uboWrite{};
    uboWrite.sType           = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
    uboWrite.dstSet          = m_descriptorSet;
    uboWrite.dstBinding      = 0;
    uboWrite.descriptorCount = 1;
    uboWrite.descriptorType  = VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER;
    uboWrite.pBufferInfo     = &bufInfo;
    vkUpdateDescriptorSets(m_device, 1, &uboWrite, 0, nullptr);

    // ── set = 1: per-mesh combined image sampler ──────────────────────────────
    VkDescriptorSetLayoutBinding texBinding{};
    texBinding.binding         = 0;
    texBinding.descriptorType  = VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER;
    texBinding.descriptorCount = 1;
    texBinding.stageFlags      = VK_SHADER_STAGE_FRAGMENT_BIT;

    VkDescriptorSetLayoutCreateInfo texLci{};
    texLci.sType        = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO;
    texLci.bindingCount = 1;
    texLci.pBindings    = &texBinding;
    vkCreateDescriptorSetLayout(m_device, &texLci, nullptr, &m_textureSetLayout);

    // Pool supports up to 64 image inputs; FREE_SET_BIT allows individual cleanup.
    VkDescriptorPoolSize texPs{};
    texPs.type            = VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER;
    texPs.descriptorCount = 64;

    VkDescriptorPoolCreateInfo texPci{};
    texPci.sType         = VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO;
    texPci.flags         = VK_DESCRIPTOR_POOL_CREATE_FREE_DESCRIPTOR_SET_BIT;
    texPci.poolSizeCount = 1;
    texPci.pPoolSizes    = &texPs;
    texPci.maxSets       = 64;
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

    VkPipelineColorBlendAttachmentState blendAttach{};
    blendAttach.blendEnable = VK_TRUE;
    blendAttach.srcColorBlendFactor = VK_BLEND_FACTOR_SRC_ALPHA;
    blendAttach.dstColorBlendFactor = VK_BLEND_FACTOR_ONE_MINUS_SRC_ALPHA;
    blendAttach.colorBlendOp = VK_BLEND_OP_ADD;
    blendAttach.srcAlphaBlendFactor = VK_BLEND_FACTOR_ONE;
    blendAttach.dstAlphaBlendFactor = VK_BLEND_FACTOR_ONE_MINUS_SRC_ALPHA;
    blendAttach.alphaBlendOp = VK_BLEND_OP_ADD;
    blendAttach.colorWriteMask =
        VK_COLOR_COMPONENT_R_BIT | VK_COLOR_COMPONENT_G_BIT |
        VK_COLOR_COMPONENT_B_BIT | VK_COLOR_COMPONENT_A_BIT;

    VkPipelineColorBlendStateCreateInfo blend{};
    blend.sType = VK_STRUCTURE_TYPE_PIPELINE_COLOR_BLEND_STATE_CREATE_INFO;
    blend.attachmentCount = 1;
    blend.pAttachments = &blendAttach;

    VkPushConstantRange pcRange{};
    pcRange.stageFlags = VK_SHADER_STAGE_FRAGMENT_BIT;
    pcRange.offset     = 0;
    pcRange.size       = 16; // 4 floats: hw, hh, r, sw

    VkDescriptorSetLayout setLayouts[] = {m_descriptorSetLayout, m_textureSetLayout};

    VkPipelineLayoutCreateInfo layoutCI{};
    layoutCI.sType                  = VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO;
    layoutCI.setLayoutCount         = 2;
    layoutCI.pSetLayouts            = setLayouts;
    layoutCI.pushConstantRangeCount = 1;
    layoutCI.pPushConstantRanges    = &pcRange;
    vkCreatePipelineLayout(m_device, &layoutCI, nullptr, &m_pipelineLayout);

    VkGraphicsPipelineCreateInfo ci{};
    ci.sType = VK_STRUCTURE_TYPE_GRAPHICS_PIPELINE_CREATE_INFO;
    ci.stageCount = 2;
    ci.pStages = stages;
    ci.pVertexInputState = &vi;
    ci.pInputAssemblyState = &ia;
    ci.pViewportState = &vs;
    ci.pRasterizationState = &rs;
    ci.pMultisampleState = &ms;
    ci.pColorBlendState = &blend;
    ci.pDynamicState = &dyn;
    ci.layout = m_pipelineLayout;
    ci.renderPass = m_renderPass;

    bool ok = vkCreateGraphicsPipelines(
                  m_device, VK_NULL_HANDLE, 1, &ci, nullptr, &m_pipeline
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

static constexpr VkDeviceSize MAX_VERTEX_BUFFER_SIZE = sizeof(Vertex) * 65536;
static constexpr VkDeviceSize MAX_INDEX_BUFFER_SIZE = sizeof(uint16_t) * 65536;

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
    ci.sType           = VK_STRUCTURE_TYPE_FRAMEBUFFER_CREATE_INFO;
    ci.renderPass      = m_renderPass;
    ci.attachmentCount = 2;
    ci.width           = m_swapExtent.width;
    ci.height          = m_swapExtent.height;
    ci.layers          = 1;

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
static void runOneShot(VkDevice device, VkCommandPool pool, VkQueue queue,
                       const std::function<void(VkCommandBuffer)>& fn)
{
    VkCommandBufferAllocateInfo ai{};
    ai.sType              = VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO;
    ai.commandPool        = pool;
    ai.level              = VK_COMMAND_BUFFER_LEVEL_PRIMARY;
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
    si.sType              = VK_STRUCTURE_TYPE_SUBMIT_INFO;
    si.commandBufferCount = 1;
    si.pCommandBuffers    = &cb;
    vkQueueSubmit(queue, 1, &si, VK_NULL_HANDLE);
    vkQueueWaitIdle(queue);

    vkFreeCommandBuffers(device, pool, 1, &cb);
}

void VC::VulkanWidget::transitionImageLayout(VkImage image, VkImageLayout from, VkImageLayout to)
{
    runOneShot(m_device, m_commandPool, m_graphicsQueue, [&](VkCommandBuffer cb) {
        VkImageMemoryBarrier barrier{};
        barrier.sType               = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER;
        barrier.oldLayout           = from;
        barrier.newLayout           = to;
        barrier.srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
        barrier.dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
        barrier.image               = image;
        barrier.subresourceRange    = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1};

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
        region.imageExtent      = {w, h, 1};
        vkCmdCopyBufferToImage(cb, buf, image, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, 1, &region);
    });
}

VkDescriptorSet VC::VulkanWidget::uploadTexture(const cv::Mat& mat)
{
    uint32_t     w         = static_cast<uint32_t>(mat.cols);
    uint32_t     h         = static_cast<uint32_t>(mat.rows);
    VkDeviceSize imageSize = static_cast<VkDeviceSize>(w * h * 4);

    // ── Staging buffer ────────────────────────────────────────────────────────
    VkBuffer       stagingBuf = VK_NULL_HANDLE;
    VkDeviceMemory stagingMem = VK_NULL_HANDLE;
    createBuffer(m_device, imageSize,
        VK_BUFFER_USAGE_TRANSFER_SRC_BIT,
        stagingBuf, stagingMem,
        [this](uint32_t f, VkMemoryPropertyFlags p) { return findMemoryType(f, p); });

    void* data;
    vkMapMemory(m_device, stagingMem, 0, imageSize, 0, &data);
    std::memcpy(data, mat.data, static_cast<size_t>(imageSize));
    vkUnmapMemory(m_device, stagingMem);

    // ── VkImage ───────────────────────────────────────────────────────────────
    TextureResource tex{};

    VkImageCreateInfo ici{};
    ici.sType         = VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO;
    ici.imageType     = VK_IMAGE_TYPE_2D;
    ici.format        = VK_FORMAT_B8G8R8A8_UNORM; // matches OpenCV BGRA layout
    ici.extent        = {w, h, 1};
    ici.mipLevels     = 1;
    ici.arrayLayers   = 1;
    ici.samples       = VK_SAMPLE_COUNT_1_BIT;
    ici.tiling        = VK_IMAGE_TILING_OPTIMAL;
    ici.usage         = VK_IMAGE_USAGE_TRANSFER_DST_BIT | VK_IMAGE_USAGE_SAMPLED_BIT;
    ici.sharingMode   = VK_SHARING_MODE_EXCLUSIVE;
    ici.initialLayout = VK_IMAGE_LAYOUT_UNDEFINED;
    vkCreateImage(m_device, &ici, nullptr, &tex.image);

    VkMemoryRequirements memReq;
    vkGetImageMemoryRequirements(m_device, tex.image, &memReq);

    VkMemoryAllocateInfo mai{};
    mai.sType           = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
    mai.allocationSize  = memReq.size;
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
    ivci.sType            = VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO;
    ivci.image            = tex.image;
    ivci.viewType         = VK_IMAGE_VIEW_TYPE_2D;
    ivci.format           = VK_FORMAT_B8G8R8A8_UNORM;
    ivci.subresourceRange = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1};
    vkCreateImageView(m_device, &ivci, nullptr, &tex.view);

    VkSamplerCreateInfo sci{};
    sci.sType        = VK_STRUCTURE_TYPE_SAMPLER_CREATE_INFO;
    sci.magFilter    = VK_FILTER_LINEAR;
    sci.minFilter    = VK_FILTER_LINEAR;
    sci.addressModeU = VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE;
    sci.addressModeV = VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE;
    sci.addressModeW = VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE;
    sci.maxLod       = 0.f;
    vkCreateSampler(m_device, &sci, nullptr, &tex.sampler);

    // ── Descriptor set ────────────────────────────────────────────────────────
    VkDescriptorSetAllocateInfo dsAi{};
    dsAi.sType              = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO;
    dsAi.descriptorPool     = m_texturePool;
    dsAi.descriptorSetCount = 1;
    dsAi.pSetLayouts        = &m_textureSetLayout;

    VkDescriptorSet descSet = VK_NULL_HANDLE;
    vkAllocateDescriptorSets(m_device, &dsAi, &descSet);

    VkDescriptorImageInfo imgInfo{};
    imgInfo.imageLayout = VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL;
    imgInfo.imageView   = tex.view;
    imgInfo.sampler     = tex.sampler;

    VkWriteDescriptorSet dsWrite{};
    dsWrite.sType           = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
    dsWrite.dstSet          = descSet;
    dsWrite.dstBinding      = 0;
    dsWrite.descriptorCount = 1;
    dsWrite.descriptorType  = VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER;
    dsWrite.pImageInfo      = &imgInfo;
    vkUpdateDescriptorSets(m_device, 1, &dsWrite, 0, nullptr);

    m_textures.push_back(tex);
    return descSet;
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
            VkDeviceSize iSize = sizeof(uint16_t) * m_indices.size();
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

    VkClearValue clearValues[2]{};
    clearValues[0] = {{{0.2f, 0.2f, 0.2f, 1.0f}}}; // MSAA attachment clear
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
    vkCmdBindPipeline(cb, VK_PIPELINE_BIND_POINT_GRAPHICS, m_pipeline);
    vkCmdBindDescriptorSets(cb, VK_PIPELINE_BIND_POINT_GRAPHICS, m_pipelineLayout, 0, 1, &m_descriptorSet, 0, nullptr);

    VkBuffer     buffers[] = {m_vertexBuffer};
    VkDeviceSize offsets[] = {0};
    vkCmdBindVertexBuffers(cb, 0, 1, buffers, offsets);

    if (!m_indices.empty()) {
        vkCmdBindIndexBuffer(cb, m_indexBuffer, 0, VK_INDEX_TYPE_UINT16);

        // Bind the default (1×1 white) texture at set=1 before the draw loop.
        // Textured meshes will rebind their own descriptor set below.
        vkCmdBindDescriptorSets(cb, VK_PIPELINE_BIND_POINT_GRAPHICS, m_pipelineLayout, 1, 1, &m_defaultTextureSet, 0, nullptr);

        for (size_t i = 0; i < m_meshes.size(); ++i) {
            const Mesh&         mesh = m_meshes[i];
            const MeshDrawInfo& info = m_meshDrawInfos[i];

            if (mesh.hasTexture && mesh.textureDescriptor != VK_NULL_HANDLE) {
                vkCmdBindDescriptorSets(cb, VK_PIPELINE_BIND_POINT_GRAPHICS, m_pipelineLayout, 1, 1, &mesh.textureDescriptor, 0, nullptr);
            } else {
                vkCmdBindDescriptorSets(cb, VK_PIPELINE_BIND_POINT_GRAPHICS, m_pipelineLayout, 1, 1, &m_defaultTextureSet, 0, nullptr);
            }

            if (!mesh.pushConstantData.empty()) {
                vkCmdPushConstants(
                    cb, m_pipelineLayout, VK_SHADER_STAGE_FRAGMENT_BIT,
                    0, static_cast<uint32_t>(mesh.pushConstantData.size()),
                    mesh.pushConstantData.data()
                );
            }
            vkCmdDrawIndexed(cb, info.indexCount, 1, info.firstIndex, 0, 0);
        }
    }

    vkCmdEndRenderPass(cb);
    // Render pass resolved MSAA → swapchain image, leaving it in TRANSFER_SRC_OPTIMAL.
    // Transition it to PRESENT_SRC_KHR so the compositor can display it.

    VkImageMemoryBarrier toPresent{};
    toPresent.sType               = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER;
    toPresent.srcAccessMask       = VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT;
    toPresent.dstAccessMask       = 0;
    toPresent.oldLayout           = VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL;
    toPresent.newLayout           = VK_IMAGE_LAYOUT_PRESENT_SRC_KHR;
    toPresent.srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
    toPresent.dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
    toPresent.image               = m_swapImages[imageIndex];
    toPresent.subresourceRange    = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1};
    vkCmdPipelineBarrier(cb,
        VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT,
        VK_PIPELINE_STAGE_BOTTOM_OF_PIPE_BIT,
        0, 0, nullptr, 0, nullptr, 1, &toPresent);

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
            void* data;
            vkMapMemory(m_device, m_vertexMemory, 0, sz, 0, &data);
            memcpy(data, m_vertices.data(), sz);
            vkUnmapMemory(m_device, m_vertexMemory);
        }
        if (!m_indices.empty()) {
            VkDeviceSize sz = sizeof(uint16_t) * m_indices.size();
            void* data;
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
    clearValues[0] = {{{0.2f, 0.2f, 0.2f, 1.0f}}};
    VkViewport   vp{0, 0, (float)m_swapExtent.width, (float)m_swapExtent.height, 0, 1};
    VkRect2D     sc{{0, 0}, m_swapExtent};

    VkRenderPassBeginInfo rpi{};
    rpi.sType             = VK_STRUCTURE_TYPE_RENDER_PASS_BEGIN_INFO;
    rpi.renderPass        = m_renderPass;
    rpi.framebuffer       = m_framebuffers.back();
    rpi.renderArea.extent = m_swapExtent;
    rpi.clearValueCount   = 2;
    rpi.pClearValues      = clearValues;

    vkCmdBeginRenderPass(m_commandBuffer, &rpi, VK_SUBPASS_CONTENTS_INLINE);
    vkCmdSetViewport(m_commandBuffer, 0, 1, &vp);
    vkCmdSetScissor(m_commandBuffer, 0, 1, &sc);
    vkCmdBindPipeline(m_commandBuffer, VK_PIPELINE_BIND_POINT_GRAPHICS, m_pipeline);
    vkCmdBindDescriptorSets(m_commandBuffer, VK_PIPELINE_BIND_POINT_GRAPHICS, m_pipelineLayout, 0, 1, &m_descriptorSet, 0, nullptr);

    VkBuffer     buffers[] = {m_vertexBuffer};
    VkDeviceSize offsets[] = {0};
    vkCmdBindVertexBuffers(m_commandBuffer, 0, 1, buffers, offsets);

    if (!m_indices.empty()) {
        vkCmdBindIndexBuffer(m_commandBuffer, m_indexBuffer, 0, VK_INDEX_TYPE_UINT16);
        vkCmdBindDescriptorSets(m_commandBuffer, VK_PIPELINE_BIND_POINT_GRAPHICS, m_pipelineLayout, 1, 1, &m_defaultTextureSet, 0, nullptr);

        for (size_t i = 0; i < m_meshes.size(); ++i) {
            const Mesh&         mesh = m_meshes[i];
            const MeshDrawInfo& info = m_meshDrawInfos[i];
            if (mesh.hasTexture && mesh.textureDescriptor != VK_NULL_HANDLE) {
                vkCmdBindDescriptorSets(m_commandBuffer, VK_PIPELINE_BIND_POINT_GRAPHICS, m_pipelineLayout, 1, 1, &mesh.textureDescriptor, 0, nullptr);
            } else {
                vkCmdBindDescriptorSets(m_commandBuffer, VK_PIPELINE_BIND_POINT_GRAPHICS, m_pipelineLayout, 1, 1, &m_defaultTextureSet, 0, nullptr);
            }
            if (!mesh.pushConstantData.empty()) {
                vkCmdPushConstants(m_commandBuffer, m_pipelineLayout, VK_SHADER_STAGE_FRAGMENT_BIT,
                    0, static_cast<uint32_t>(mesh.pushConstantData.size()), mesh.pushConstantData.data());
            }
            vkCmdDrawIndexed(m_commandBuffer, info.indexCount, 1, info.firstIndex, 0, 0);
        }
    }
    vkCmdEndRenderPass(m_commandBuffer);
    // m_resolveImage is now in TRANSFER_SRC_OPTIMAL (render pass finalLayout).

    // ── Transition readback image UNDEFINED → TRANSFER_DST ───────────────
    VkImageMemoryBarrier toReadDst{};
    toReadDst.sType               = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER;
    toReadDst.srcAccessMask       = 0;
    toReadDst.dstAccessMask       = VK_ACCESS_TRANSFER_WRITE_BIT;
    toReadDst.oldLayout           = VK_IMAGE_LAYOUT_UNDEFINED;
    toReadDst.newLayout           = VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL;
    toReadDst.srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
    toReadDst.dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
    toReadDst.image               = m_readbackImage;
    toReadDst.subresourceRange    = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1};
    vkCmdPipelineBarrier(m_commandBuffer, VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT,
                         0, 0, nullptr, 0, nullptr, 1, &toReadDst);

    // ── Blit resolve image → readback (same size, copies resolved pixels) ─
    VkImageBlit blit{};
    blit.srcSubresource = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 0, 1};
    blit.srcOffsets[0]  = {0, 0, 0};
    blit.srcOffsets[1]  = {(int32_t)m_swapExtent.width, (int32_t)m_swapExtent.height, 1};
    blit.dstSubresource = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 0, 1};
    blit.dstOffsets[0]  = {0, 0, 0};
    blit.dstOffsets[1]  = {(int32_t)m_swapExtent.width, (int32_t)m_swapExtent.height, 1};
    vkCmdBlitImage(m_commandBuffer, m_resolveImage, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,
                   m_readbackImage, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
                   1, &blit, VK_FILTER_LINEAR);

    // ── Transition readback TRANSFER_DST → GENERAL (host read) ───────────
    VkImageMemoryBarrier toGeneral{};
    toGeneral.sType               = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER;
    toGeneral.srcAccessMask       = VK_ACCESS_TRANSFER_WRITE_BIT;
    toGeneral.dstAccessMask       = VK_ACCESS_HOST_READ_BIT;
    toGeneral.oldLayout           = VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL;
    toGeneral.newLayout           = VK_IMAGE_LAYOUT_GENERAL;
    toGeneral.srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
    toGeneral.dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
    toGeneral.image               = m_readbackImage;
    toGeneral.subresourceRange    = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1};
    vkCmdPipelineBarrier(m_commandBuffer, VK_PIPELINE_STAGE_TRANSFER_BIT, VK_PIPELINE_STAGE_HOST_BIT,
                         0, 0, nullptr, 0, nullptr, 1, &toGeneral);

    vkEndCommandBuffer(m_commandBuffer);

    // ── Submit and wait ───────────────────────────────────────────────────
    VkSubmitInfo si{};
    si.sType              = VK_STRUCTURE_TYPE_SUBMIT_INFO;
    si.commandBufferCount = 1;
    si.pCommandBuffers    = &m_commandBuffer;
    vkQueueSubmit(m_graphicsQueue, 1, &si, VK_NULL_HANDLE);
    vkQueueWaitIdle(m_graphicsQueue);

    // ── Map and copy to cv::Mat ───────────────────────────────────────────
    VkImageSubresource    subRes{VK_IMAGE_ASPECT_COLOR_BIT, 0, 0};
    VkSubresourceLayout   layout{};
    vkGetImageSubresourceLayout(m_device, m_readbackImage, &subRes, &layout);

    void* data;
    vkMapMemory(m_device, m_readbackMemory, 0, VK_WHOLE_SIZE, 0, &data);

    uint32_t   W = m_swapExtent.width;
    uint32_t   H = m_swapExtent.height;
    cv::Mat    result(H, W, CV_8UC4);
    uint8_t*   src = static_cast<uint8_t*>(data) + layout.offset;
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

    // Advance the animation and upload new geometry before touching the GPU.
    if (m_frameCallback) {
        setMeshes(m_frameCallback());
    }

    // Block the CPU until the GPU has finished the previous frame so we don't
    // overwrite the command buffer while it is still in use.
    vkWaitForFences(m_device, 1, &m_inFlightFence, VK_TRUE, UINT64_MAX);
    vkResetFences(m_device, 1, &m_inFlightFence);

    uint32_t imageIndex;
    VkResult res = vkAcquireNextImageKHR(m_device, m_swapchain, UINT64_MAX, m_imageAvailableSemaphore, VK_NULL_HANDLE, &imageIndex);
    if (res == VK_ERROR_OUT_OF_DATE_KHR) {
        recreateSwapchain();
        return;
    }

    vkResetCommandBuffer(m_commandBuffer, 0);
    recordCommandBuffer(m_commandBuffer, imageIndex);

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

    vkDestroyPipeline(m_device, m_pipeline, nullptr);
    vkDestroyPipelineLayout(m_device, m_pipelineLayout, nullptr);

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
