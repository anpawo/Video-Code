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

#include "vulkan/MetalSurface.hpp"   // CAMetalLayer bridge (macOS only)
#include "vulkan/ShaderCompiler.hpp" // Runtime GLSL → SPIR-V via glslang

#include <fstream>
#include <sstream>

// ============================================================================
// loadShaderSource
//   Reads a GLSL file from assets/shaders/quadraticBezier/ at runtime.
//   Compiled to SPIR-V by compileGLSL() so tweaks don't need a separate step.
// ============================================================================

static std::string loadShaderSource(const std::string &filename)
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

                VkPhysicalDeviceProperties props;
                vkGetPhysicalDeviceProperties(pd, &props);

                // Pick the highest MSAA sample count the device supports
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
//   Allocates a 2× offscreen image used as the render target.
//   The render pass draws here; recordCommandBuffer() blits it down to the
//   swapchain image with VK_FILTER_LINEAR for a free 4-sample box filter.
// ============================================================================

bool VC::VulkanWidget::createSsaaResources()
{
    m_ssaaExtent = {m_swapExtent.width * 4, m_swapExtent.height * 4};

    VkImageCreateInfo ici{};
    ici.sType = VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO;
    ici.imageType = VK_IMAGE_TYPE_2D;
    ici.format = m_swapFormat;
    ici.extent = {m_ssaaExtent.width, m_ssaaExtent.height, 1};
    ici.mipLevels = 1;
    ici.arrayLayers = 1;
    ici.samples = VK_SAMPLE_COUNT_1_BIT;
    ici.tiling = VK_IMAGE_TILING_OPTIMAL;
    ici.usage = VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT | VK_IMAGE_USAGE_TRANSFER_SRC_BIT;
    ici.sharingMode = VK_SHARING_MODE_EXCLUSIVE;
    ici.initialLayout = VK_IMAGE_LAYOUT_UNDEFINED;

    if (vkCreateImage(m_device, &ici, nullptr, &m_ssaaImage) != VK_SUCCESS) {
        return false;
    }

    VkMemoryRequirements memReq;
    vkGetImageMemoryRequirements(m_device, m_ssaaImage, &memReq);

    VkMemoryAllocateInfo ai{};
    ai.sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
    ai.allocationSize = memReq.size;
    ai.memoryTypeIndex = findMemoryType(memReq.memoryTypeBits, VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT);

    if (vkAllocateMemory(m_device, &ai, nullptr, &m_ssaaMemory) != VK_SUCCESS) {
        return false;
    }
    vkBindImageMemory(m_device, m_ssaaImage, m_ssaaMemory, 0);

    VkImageViewCreateInfo ivci{};
    ivci.sType = VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO;
    ivci.image = m_ssaaImage;
    ivci.viewType = VK_IMAGE_VIEW_TYPE_2D;
    ivci.format = m_swapFormat;
    ivci.subresourceRange = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1};

    return vkCreateImageView(m_device, &ivci, nullptr, &m_ssaaImageView) == VK_SUCCESS;
}

void VC::VulkanWidget::destroySsaaResources()
{
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
// Step 6: createRenderPass
//   Single colour attachment: clear to black on load, store for presentation.
// ============================================================================

bool VC::VulkanWidget::createRenderPass()
{
    VkAttachmentDescription colorAttachment{};
    colorAttachment.format = m_swapFormat;
    colorAttachment.samples = VK_SAMPLE_COUNT_1_BIT;
    colorAttachment.loadOp = VK_ATTACHMENT_LOAD_OP_CLEAR;
    colorAttachment.storeOp = VK_ATTACHMENT_STORE_OP_STORE;
    colorAttachment.stencilLoadOp = VK_ATTACHMENT_LOAD_OP_DONT_CARE;
    colorAttachment.stencilStoreOp = VK_ATTACHMENT_STORE_OP_DONT_CARE;
    colorAttachment.initialLayout = VK_IMAGE_LAYOUT_UNDEFINED;
    colorAttachment.finalLayout = VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL;

    VkAttachmentReference colorRef{};
    colorRef.attachment = 0;
    colorRef.layout = VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL;

    VkSubpassDescription subpass{};
    subpass.pipelineBindPoint = VK_PIPELINE_BIND_POINT_GRAPHICS;
    subpass.colorAttachmentCount = 1;
    subpass.pColorAttachments = &colorRef;

    VkSubpassDependency dep{};
    dep.srcSubpass = VK_SUBPASS_EXTERNAL;
    dep.srcStageMask = VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT;
    dep.dstStageMask = VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT;
    dep.dstAccessMask = VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT;

    VkRenderPassCreateInfo ci{};
    ci.sType = VK_STRUCTURE_TYPE_RENDER_PASS_CREATE_INFO;
    ci.attachmentCount = 1;
    ci.pAttachments = &colorAttachment;
    ci.subpassCount = 1;
    ci.pSubpasses = &subpass;
    ci.dependencyCount = 1;
    ci.pDependencies = &dep;

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
    VkDescriptorSetLayoutBinding b{};
    b.binding = 0;
    b.descriptorType = VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER;
    b.descriptorCount = 1;
    b.stageFlags = VK_SHADER_STAGE_FRAGMENT_BIT;

    VkDescriptorSetLayoutCreateInfo lci{};
    lci.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO;
    lci.bindingCount = 1;
    lci.pBindings = &b;
    vkCreateDescriptorSetLayout(m_device, &lci, nullptr, &m_descriptorSetLayout);

    VkDescriptorPoolSize ps{};
    ps.type = VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER;
    ps.descriptorCount = 1;

    VkDescriptorPoolCreateInfo pci{};
    pci.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO;
    pci.poolSizeCount = 1;
    pci.pPoolSizes = &ps;
    pci.maxSets = 1;
    vkCreateDescriptorPool(m_device, &pci, nullptr, &m_descriptorPool);

    VkDescriptorSetAllocateInfo ai{};
    ai.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO;
    ai.descriptorPool = m_descriptorPool;
    ai.descriptorSetCount = 1;
    ai.pSetLayouts = &m_descriptorSetLayout;
    vkAllocateDescriptorSets(m_device, &ai, &m_descriptorSet);

    VkDescriptorBufferInfo bi{};
    bi.buffer = m_uniformBuffer;
    bi.offset = 0;
    bi.range = sizeof(UniformData);

    VkWriteDescriptorSet w{};
    w.sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
    w.dstSet = m_descriptorSet;
    w.dstBinding = 0;
    w.descriptorCount = 1;
    w.descriptorType = VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER;
    w.pBufferInfo = &bi;
    vkUpdateDescriptorSets(m_device, 1, &w, 0, nullptr);

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
    ms.rasterizationSamples = VK_SAMPLE_COUNT_1_BIT;

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

    VkPipelineLayoutCreateInfo layoutCI{};
    layoutCI.sType                  = VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO;
    layoutCI.setLayoutCount         = 1;
    layoutCI.pSetLayouts            = &m_descriptorSetLayout;
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
//   Single framebuffer at 2× (SSAA) resolution backed by m_ssaaImageView.
//   The render pass renders here; a blit in recordCommandBuffer() downsamples
//   to the swapchain image.
// ============================================================================

bool VC::VulkanWidget::createFramebuffers()
{
    VkImageView             attachments[1] = {m_ssaaImageView};
    VkFramebufferCreateInfo ci{};
    ci.sType = VK_STRUCTURE_TYPE_FRAMEBUFFER_CREATE_INFO;
    ci.renderPass = m_renderPass;
    ci.attachmentCount = 1;
    ci.pAttachments = attachments;
    ci.width = m_ssaaExtent.width;
    ci.height = m_ssaaExtent.height;
    ci.layers = 1;

    m_framebuffers.resize(1);
    return vkCreateFramebuffer(m_device, &ci, nullptr, &m_framebuffers[0]) == VK_SUCCESS;
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

    VkClearValue clearColor = {{{0.2f, 0.2f, 0.2f, 1.0f}}}; // Match Manim default background (#333333)
    // VkClearValue clearColor = {{{0.1f, 0.0f, 0.2f, 1.0f}}}; // dark purple — confirms Vulkan is rendering

    VkViewport vp{0, 0, (float)m_ssaaExtent.width, (float)m_ssaaExtent.height, 0, 1};
    VkRect2D   sc{{0, 0}, m_ssaaExtent};

    VkRenderPassBeginInfo rpi{};
    rpi.sType = VK_STRUCTURE_TYPE_RENDER_PASS_BEGIN_INFO;
    rpi.renderPass = m_renderPass;
    rpi.framebuffer = m_framebuffers[0];
    rpi.renderArea.extent = m_ssaaExtent;
    rpi.clearValueCount = 1;
    rpi.pClearValues = &clearColor;

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

        for (size_t i = 0; i < m_meshes.size(); ++i) {
            const Mesh&         mesh = m_meshes[i];
            const MeshDrawInfo& info = m_meshDrawInfos[i];

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
    // render pass left SSAA image in TRANSFER_SRC_OPTIMAL (finalLayout).
    // Transition the swapchain image UNDEFINED → TRANSFER_DST_OPTIMAL, blit, then → PRESENT_SRC_KHR.

    VkImageMemoryBarrier toDst{};
    toDst.sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER;
    toDst.srcAccessMask = 0;
    toDst.dstAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT;
    toDst.oldLayout = VK_IMAGE_LAYOUT_UNDEFINED;
    toDst.newLayout = VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL;
    toDst.srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
    toDst.dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
    toDst.image = m_swapImages[imageIndex];
    toDst.subresourceRange = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1};
    vkCmdPipelineBarrier(cb, VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT, 0, 0, nullptr, 0, nullptr, 1, &toDst);

    VkImageBlit region{};
    region.srcSubresource = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 0, 1};
    region.srcOffsets[0] = {0, 0, 0};
    region.srcOffsets[1] = {(int32_t)m_ssaaExtent.width, (int32_t)m_ssaaExtent.height, 1};
    region.dstSubresource = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 0, 1};
    region.dstOffsets[0] = {0, 0, 0};
    region.dstOffsets[1] = {(int32_t)m_swapExtent.width, (int32_t)m_swapExtent.height, 1};
    vkCmdBlitImage(cb, m_ssaaImage, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL, m_swapImages[imageIndex], VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, 1, &region, VK_FILTER_LINEAR);

    VkImageMemoryBarrier toPresent{};
    toPresent.sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER;
    toPresent.srcAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT;
    toPresent.dstAccessMask = 0;
    toPresent.oldLayout = VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL;
    toPresent.newLayout = VK_IMAGE_LAYOUT_PRESENT_SRC_KHR;
    toPresent.srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
    toPresent.dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
    toPresent.image = m_swapImages[imageIndex];
    toPresent.subresourceRange = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1};
    vkCmdPipelineBarrier(cb, VK_PIPELINE_STAGE_TRANSFER_BIT, VK_PIPELINE_STAGE_BOTTOM_OF_PIPE_BIT, 0, 0, nullptr, 0, nullptr, 1, &toPresent);

    vkEndCommandBuffer(cb);
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

    for (auto iv : m_swapImageViews) {
        vkDestroyImageView(m_device, iv, nullptr);
    }
    vkDestroySwapchainKHR(m_device, m_swapchain, nullptr);

    createSwapchain();
    createSsaaResources();
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

    vkDestroyPipeline(m_device, m_pipeline, nullptr);
    vkDestroyPipelineLayout(m_device, m_pipelineLayout, nullptr);

    vkDestroyDescriptorPool(m_device, m_descriptorPool, nullptr); // frees sets implicitly
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
