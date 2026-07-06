/*
** EPITECH PROJECT, 2026
** video-code
** File description:
** VulkanHeadlessRenderer
*/

#include "vulkan/VulkanHeadlessRenderer.hpp"

#include <algorithm>
#include <array>
#include <chrono>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <functional>
#include <iostream>
#include <sstream>

#include "vulkan/EffectResolver.hpp"
#include "vulkan/LutAtlas.hpp"
#include "vulkan/ShaderCompiler.hpp"
#include "vulkan/Vertex.hpp"

// ---------------------------------------------------------------------------
// loadShaderSource — read GLSL from assets/shaders/{subfolder}/{filename}
// ---------------------------------------------------------------------------

static std::string loadShaderSource(const std::string& filename)
{
    std::string   path = std::string(SHADER_DIR) + "/quadraticBezier/" + filename;
    std::ifstream f(path);
    if (!f.is_open()) return {};
    std::ostringstream ss;
    ss << f.rdbuf();
    return ss.str();
}

static std::string loadEffectShader(const std::string& folder, const std::string& file)
{
    std::string   path = std::string(SHADER_DIR) + "/" + folder + "/" + file;
    std::ifstream f(path);
    if (!f.is_open()) return {};
    std::ostringstream ss;
    ss << f.rdbuf();
    return ss.str();
}

// Push constants shared by all effect passes
struct EffectPC
{
    float texelX;
    float texelY;
    float p[8];
};

// Explicit image memory barrier between effect passes.
// More reliable than subpass external dependencies on MoltenVK / Metal.
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

// Two-image barrier covering both RAW (written→read) and WAR (read→write) at the same point.
static void effectBarrier2(VkCommandBuffer cb,
                           VkImage         readImg,  // image that was the write target — now being made readable
                           VkImage         writeImg) // image that was the read source — now being made writable
{
    VkImageMemoryBarrier bs[2]{};
    // RAW: previous COLOR_ATTACHMENT write → upcoming FRAGMENT_SHADER read
    bs[0].sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER;
    bs[0].srcAccessMask = VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT;
    bs[0].dstAccessMask = VK_ACCESS_SHADER_READ_BIT;
    bs[0].oldLayout = VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL;
    bs[0].newLayout = VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL;
    bs[0].srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
    bs[0].dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
    bs[0].image = readImg;
    bs[0].subresourceRange = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1};
    // WAR: previous FRAGMENT_SHADER read → upcoming COLOR_ATTACHMENT write
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

// ---------------------------------------------------------------------------
// createBuffer helper (file-local, same as VulkanWidget.cpp)
// ---------------------------------------------------------------------------

static bool makeBuffer(
    VkDevice device, VkDeviceSize size, VkBufferUsageFlags usage,
    VkBuffer& outBuf, VkDeviceMemory& outMem,
    std::function<uint32_t(uint32_t, VkMemoryPropertyFlags)> findMem
)
{
    VkBufferCreateInfo bi{};
    bi.sType = VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO;
    bi.size = size;
    bi.usage = usage;
    bi.sharingMode = VK_SHARING_MODE_EXCLUSIVE;
    if (vkCreateBuffer(device, &bi, nullptr, &outBuf) != VK_SUCCESS) return false;

    VkMemoryRequirements req;
    vkGetBufferMemoryRequirements(device, outBuf, &req);

    VkMemoryAllocateInfo ai{};
    ai.sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
    ai.allocationSize = req.size;
    ai.memoryTypeIndex = findMem(req.memoryTypeBits, VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT);
    if (vkAllocateMemory(device, &ai, nullptr, &outMem) != VK_SUCCESS) return false;
    vkBindBufferMemory(device, outBuf, outMem, 0);
    return true;
}

// ---------------------------------------------------------------------------
// runOneShot helper — submit a command buffer and wait
// ---------------------------------------------------------------------------

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

// ===========================================================================
// Constructor / Destructor
// ===========================================================================

VC::VulkanHeadlessRenderer::VulkanHeadlessRenderer(uint32_t width, uint32_t height)
    : m_width(width)
    , m_height(height)
    , m_extent{width, height}
    , m_ssaaExtent{width * 4, height * 4}
{
}

VC::VulkanHeadlessRenderer::~VulkanHeadlessRenderer()
{
    cleanup();
}

// ===========================================================================
// init — run all setup steps in order
// ===========================================================================

bool VC::VulkanHeadlessRenderer::init()
{
#define STEP(fn)                                                       \
    if (!(fn)) {                                                       \
        std::cerr << "VulkanHeadlessRenderer::init: " #fn " failed\n"; \
        return false;                                                  \
    }
    STEP(createInstance())
    STEP(pickPhysicalDevice())
    STEP(createDevice())
    STEP(createCommandPool())
    STEP(createSsaaResources())
    STEP(createReadbackResources())
    STEP(createRenderPass())
    STEP(createUniformBuffer())
    STEP(createDescriptorSets())
    STEP(createPipeline())
    STEP(createGeometryBuffers())
    STEP(createCommandBuffer())
    cv::Mat white(1, 1, CV_8UC4, cv::Scalar(255, 255, 255, 255));
    m_defaultTexSet = uploadTexture(white);
    if (m_defaultTexSet == VK_NULL_HANDLE) {
        std::cerr << "VulkanHeadlessRenderer::init: uploadTexture(white) failed\n";
        return false;
    }
    STEP(createEffectResources())
#undef STEP
    return true;
}

// ===========================================================================
// Step 1: createInstance — no surface extensions needed for headless
// ===========================================================================

bool VC::VulkanHeadlessRenderer::createInstance()
{
    // Enumerate available instance extensions.
    uint32_t extCount = 0;
    vkEnumerateInstanceExtensionProperties(nullptr, &extCount, nullptr);
    std::vector<VkExtensionProperties> available(extCount);
    vkEnumerateInstanceExtensionProperties(nullptr, &extCount, available.data());

    auto hasExt = [&](const char* name) {
        for (auto& e : available)
            if (strcmp(e.extensionName, name) == 0) return true;
        return false;
    };

    std::vector<const char*> extensions;
    VkInstanceCreateFlags    flags = 0;

    // On MoltenVK / macOS the portability enumeration extension is required
    // to enumerate physical devices, but only if it exists.
    if (hasExt("VK_KHR_portability_enumeration")) {
        extensions.push_back("VK_KHR_portability_enumeration");
        flags |= VK_INSTANCE_CREATE_ENUMERATE_PORTABILITY_BIT_KHR;
    }

    VkApplicationInfo appInfo{};
    appInfo.sType = VK_STRUCTURE_TYPE_APPLICATION_INFO;
    appInfo.pApplicationName = "video-code-headless";
    appInfo.apiVersion = VK_API_VERSION_1_0;

    VkInstanceCreateInfo ci{};
    ci.sType = VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO;
    ci.pApplicationInfo = &appInfo;
    ci.enabledExtensionCount = (uint32_t)extensions.size();
    ci.ppEnabledExtensionNames = extensions.data();
    ci.flags = flags;

    return vkCreateInstance(&ci, nullptr, &m_instance) == VK_SUCCESS;
}

// ===========================================================================
// Step 2: pickPhysicalDevice — any GPU with a graphics queue
// ===========================================================================

bool VC::VulkanHeadlessRenderer::pickPhysicalDevice()
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

        for (uint32_t i = 0; i < qCount; ++i) {
            if (qProps[i].queueFlags & VK_QUEUE_GRAPHICS_BIT) {
                m_physicalDevice = pd;
                m_graphicsFamily = i;
                return true;
            }
        }
    }
    return false;
}

// ===========================================================================
// Step 3: createDevice
// ===========================================================================

bool VC::VulkanHeadlessRenderer::createDevice()
{
    float                   priority = 1.0f;
    VkDeviceQueueCreateInfo qci{};
    qci.sType = VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO;
    qci.queueFamilyIndex = m_graphicsFamily;
    qci.queueCount = 1;
    qci.pQueuePriorities = &priority;

    // Only request VK_KHR_portability_subset if the device exposes it.
    uint32_t extCount = 0;
    vkEnumerateDeviceExtensionProperties(m_physicalDevice, nullptr, &extCount, nullptr);
    std::vector<VkExtensionProperties> devExts(extCount);
    vkEnumerateDeviceExtensionProperties(m_physicalDevice, nullptr, &extCount, devExts.data());

    std::vector<const char*> extensions;
    for (auto& e : devExts)
        if (strcmp(e.extensionName, "VK_KHR_portability_subset") == 0)
            extensions.push_back("VK_KHR_portability_subset");

    VkDeviceCreateInfo ci{};
    ci.sType = VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO;
    ci.queueCreateInfoCount = 1;
    ci.pQueueCreateInfos = &qci;
    ci.enabledExtensionCount = (uint32_t)extensions.size();
    ci.ppEnabledExtensionNames = extensions.data();
    if (vkCreateDevice(m_physicalDevice, &ci, nullptr, &m_device) != VK_SUCCESS)
        return false;

    vkGetDeviceQueue(m_device, m_graphicsFamily, 0, &m_graphicsQueue);
    return true;
}

// ===========================================================================
// Step 4: createSsaaResources — 4× offscreen render target
// ===========================================================================

bool VC::VulkanHeadlessRenderer::createSsaaResources()
{
    VkImageCreateInfo ici{};
    ici.sType = VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO;
    ici.imageType = VK_IMAGE_TYPE_2D;
    ici.format = VK_FORMAT_B8G8R8A8_UNORM;
    ici.extent = {m_ssaaExtent.width, m_ssaaExtent.height, 1};
    ici.mipLevels = 1;
    ici.arrayLayers = 1;
    ici.samples = VK_SAMPLE_COUNT_1_BIT;
    ici.tiling = VK_IMAGE_TILING_OPTIMAL;
    ici.usage = VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT | VK_IMAGE_USAGE_TRANSFER_SRC_BIT;
    ici.sharingMode = VK_SHARING_MODE_EXCLUSIVE;
    ici.initialLayout = VK_IMAGE_LAYOUT_UNDEFINED;
    if (vkCreateImage(m_device, &ici, nullptr, &m_ssaaImage) != VK_SUCCESS) return false;

    VkMemoryRequirements memReq;
    vkGetImageMemoryRequirements(m_device, m_ssaaImage, &memReq);
    VkMemoryAllocateInfo ai{};
    ai.sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
    ai.allocationSize = memReq.size;
    ai.memoryTypeIndex = findMemoryType(memReq.memoryTypeBits, VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT);
    if (vkAllocateMemory(m_device, &ai, nullptr, &m_ssaaMemory) != VK_SUCCESS) return false;
    vkBindImageMemory(m_device, m_ssaaImage, m_ssaaMemory, 0);

    VkImageViewCreateInfo ivci{};
    ivci.sType = VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO;
    ivci.image = m_ssaaImage;
    ivci.viewType = VK_IMAGE_VIEW_TYPE_2D;
    ivci.format = VK_FORMAT_B8G8R8A8_UNORM;
    ivci.subresourceRange = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1};
    return vkCreateImageView(m_device, &ivci, nullptr, &m_ssaaImageView) == VK_SUCCESS;
}

// ===========================================================================
// Step 5: createReadbackResources — linear host-visible image at output size
// ===========================================================================

bool VC::VulkanHeadlessRenderer::createReadbackResources()
{
    for (size_t i = 0; i < 2; ++i) {
        VkImageCreateInfo ici{};
        ici.sType = VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO;
        ici.imageType = VK_IMAGE_TYPE_2D;
        ici.format = VK_FORMAT_B8G8R8A8_UNORM;
        ici.extent = {m_extent.width, m_extent.height, 1};
        ici.mipLevels = 1;
        ici.arrayLayers = 1;
        ici.samples = VK_SAMPLE_COUNT_1_BIT;
        ici.tiling = VK_IMAGE_TILING_LINEAR;
        ici.usage = VK_IMAGE_USAGE_TRANSFER_DST_BIT;
        ici.sharingMode = VK_SHARING_MODE_EXCLUSIVE;
        ici.initialLayout = VK_IMAGE_LAYOUT_UNDEFINED;
        if (vkCreateImage(m_device, &ici, nullptr, &m_readbackImages[i]) != VK_SUCCESS) return false;

        VkMemoryRequirements memReq;
        vkGetImageMemoryRequirements(m_device, m_readbackImages[i], &memReq);
        VkMemoryAllocateInfo ai{};
        ai.sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
        ai.allocationSize = memReq.size;
        ai.memoryTypeIndex = findMemoryType(memReq.memoryTypeBits, VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT);
        if (vkAllocateMemory(m_device, &ai, nullptr, &m_readbackMemories[i]) != VK_SUCCESS) return false;
        vkBindImageMemory(m_device, m_readbackImages[i], m_readbackMemories[i], 0);
    }
    return true;
}

// ===========================================================================
// Step 6: createRenderPass
// ===========================================================================

bool VC::VulkanHeadlessRenderer::createRenderPass()
{
    VkAttachmentDescription col{};
    col.format = VK_FORMAT_B8G8R8A8_UNORM;
    col.samples = VK_SAMPLE_COUNT_1_BIT;
    col.loadOp = VK_ATTACHMENT_LOAD_OP_CLEAR;
    col.storeOp = VK_ATTACHMENT_STORE_OP_STORE;
    col.stencilLoadOp = VK_ATTACHMENT_LOAD_OP_DONT_CARE;
    col.stencilStoreOp = VK_ATTACHMENT_STORE_OP_DONT_CARE;
    col.initialLayout = VK_IMAGE_LAYOUT_UNDEFINED;
    col.finalLayout = VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL;

    VkAttachmentReference ref{0, VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL};

    VkSubpassDescription subpass{};
    subpass.pipelineBindPoint = VK_PIPELINE_BIND_POINT_GRAPHICS;
    subpass.colorAttachmentCount = 1;
    subpass.pColorAttachments = &ref;

    VkSubpassDependency dep{};
    dep.srcSubpass = VK_SUBPASS_EXTERNAL;
    dep.srcStageMask = VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT;
    dep.dstStageMask = VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT;
    dep.dstAccessMask = VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT;

    VkRenderPassCreateInfo ci{};
    ci.sType = VK_STRUCTURE_TYPE_RENDER_PASS_CREATE_INFO;
    ci.attachmentCount = 1;
    ci.pAttachments = &col;
    ci.subpassCount = 1;
    ci.pSubpasses = &subpass;
    ci.dependencyCount = 1;
    ci.pDependencies = &dep;

    if (vkCreateRenderPass(m_device, &ci, nullptr, &m_renderPass) != VK_SUCCESS) return false;

    VkImageView             attachments[] = {m_ssaaImageView};
    VkFramebufferCreateInfo fci{};
    fci.sType = VK_STRUCTURE_TYPE_FRAMEBUFFER_CREATE_INFO;
    fci.renderPass = m_renderPass;
    fci.attachmentCount = 1;
    fci.pAttachments = attachments;
    fci.width = m_ssaaExtent.width;
    fci.height = m_ssaaExtent.height;
    fci.layers = 1;
    return vkCreateFramebuffer(m_device, &fci, nullptr, &m_framebuffer) == VK_SUCCESS;
}

// ===========================================================================
// Step 7: createUniformBuffer
// ===========================================================================

bool VC::VulkanHeadlessRenderer::createUniformBuffer()
{
    struct UBO
    {
        float time, pad[3], res[2], pixelSize, pad2;
    };

    return makeBuffer(m_device, sizeof(UBO), VK_BUFFER_USAGE_UNIFORM_BUFFER_BIT, m_uniformBuffer, m_uniformMemory, [this](uint32_t f, VkMemoryPropertyFlags p) { return findMemoryType(f, p); });
}

// ===========================================================================
// Step 8: createDescriptorSets — UBO (set=0) + texture pool (set=1)
// ===========================================================================

bool VC::VulkanHeadlessRenderer::createDescriptorSets()
{
    // set=0 UBO
    VkDescriptorSetLayoutBinding uboB{};
    uboB.binding = 0;
    uboB.descriptorType = VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER;
    uboB.descriptorCount = 1;
    uboB.stageFlags = VK_SHADER_STAGE_FRAGMENT_BIT;
    VkDescriptorSetLayoutCreateInfo uboLci{VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO, nullptr, 0, 1, &uboB};
    vkCreateDescriptorSetLayout(m_device, &uboLci, nullptr, &m_uboLayout);

    VkDescriptorPoolSize       uboPs{VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER, 1};
    VkDescriptorPoolCreateInfo uboPci{VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO, nullptr, 0, 1, 1, &uboPs};
    vkCreateDescriptorPool(m_device, &uboPci, nullptr, &m_uboPool);

    VkDescriptorSetAllocateInfo uboAi{VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO, nullptr, m_uboPool, 1, &m_uboLayout};
    vkAllocateDescriptorSets(m_device, &uboAi, &m_uboSet);

    struct UBO
    {
        float time, pad[3], res[2], pixelSize, pad2;
    };

    VkDescriptorBufferInfo bufInfo{m_uniformBuffer, 0, sizeof(UBO)};
    VkWriteDescriptorSet   uboW{VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET, nullptr, m_uboSet, 0, 0, 1, VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER, nullptr, &bufInfo, nullptr};
    vkUpdateDescriptorSets(m_device, 1, &uboW, 0, nullptr);

    // set=1 texture
    VkDescriptorSetLayoutBinding texB{};
    texB.binding = 0;
    texB.descriptorType = VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER;
    texB.descriptorCount = 1;
    texB.stageFlags = VK_SHADER_STAGE_FRAGMENT_BIT;
    VkDescriptorSetLayoutCreateInfo texLci{VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO, nullptr, 0, 1, &texB};
    vkCreateDescriptorSetLayout(m_device, &texLci, nullptr, &m_texLayout);

    VkDescriptorPoolSize       texPs{VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER, 128};
    VkDescriptorPoolCreateInfo texPci{VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO, nullptr, VK_DESCRIPTOR_POOL_CREATE_FREE_DESCRIPTOR_SET_BIT, 128, 1, &texPs};
    vkCreateDescriptorPool(m_device, &texPci, nullptr, &m_texPool);

    return true;
}

// ===========================================================================
// Step 9: createPipeline
// ===========================================================================

bool VC::VulkanHeadlessRenderer::createPipeline()
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
    ms.rasterizationSamples = VK_SAMPLE_COUNT_1_BIT;

    // One color-blend attachment (and thus one full create-info) per blend mode.
    // Only pColorBlendState varies between the variants — see BlendModes.hpp.
    VkPipelineColorBlendAttachmentState blendAttach[kBlendModeCount];
    VkPipelineColorBlendStateCreateInfo blendState[kBlendModeCount]{};
    for (int m = 0; m < kBlendModeCount; ++m) {
        blendAttach[m] = blendAttachmentFor(m);
        blendState[m].sType = VK_STRUCTURE_TYPE_PIPELINE_COLOR_BLEND_STATE_CREATE_INFO;
        blendState[m].attachmentCount = 1;
        blendState[m].pAttachments = &blendAttach[m];
    }

    VkDescriptorSetLayout      setLayouts[] = {m_uboLayout, m_texLayout};
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

    bool ok = vkCreateGraphicsPipelines(m_device, VK_NULL_HANDLE, kBlendModeCount, cis, nullptr, m_pipelines) == VK_SUCCESS;
    vkDestroyShaderModule(m_device, vert, nullptr);
    vkDestroyShaderModule(m_device, frag, nullptr);
    return ok;
}

// ===========================================================================
// Step 10: createGeometryBuffers
// ===========================================================================

bool VC::VulkanHeadlessRenderer::createGeometryBuffers()
{
    auto fm = [this](uint32_t f, VkMemoryPropertyFlags p) { return findMemoryType(f, p); };
    return makeBuffer(m_device, sizeof(Vertex) * 262144, VK_BUFFER_USAGE_VERTEX_BUFFER_BIT, m_vertexBuffer, m_vertexMemory, fm) && makeBuffer(m_device, sizeof(uint32_t) * 262144, VK_BUFFER_USAGE_INDEX_BUFFER_BIT, m_indexBuffer, m_indexMemory, fm);
}

// ===========================================================================
// Step 11 / 12: createCommandPool / createCommandBuffer
// ===========================================================================

bool VC::VulkanHeadlessRenderer::createCommandPool()
{
    VkCommandPoolCreateInfo ci{};
    ci.sType = VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO;
    ci.flags = VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT;
    ci.queueFamilyIndex = m_graphicsFamily;
    return vkCreateCommandPool(m_device, &ci, nullptr, &m_commandPool) == VK_SUCCESS;
}

bool VC::VulkanHeadlessRenderer::createCommandBuffer()
{
    VkCommandBufferAllocateInfo ai{};
    ai.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO;
    ai.commandPool = m_commandPool;
    ai.level = VK_COMMAND_BUFFER_LEVEL_PRIMARY;
    ai.commandBufferCount = 1;
    if (vkAllocateCommandBuffers(m_device, &ai, &m_commandBuffer) != VK_SUCCESS) return false;

    // Signals when the frame submitted in readFrame()/flush() has finished —
    // lets the next readFrame() overlap this frame's GPU work with the
    // previous frame's readback memcpy.
    VkFenceCreateInfo fi{};
    fi.sType = VK_STRUCTURE_TYPE_FENCE_CREATE_INFO;
    return vkCreateFence(m_device, &fi, nullptr, &m_renderFence) == VK_SUCCESS;
}

// ===========================================================================
// Vulkan utilities
// ===========================================================================

uint32_t VC::VulkanHeadlessRenderer::findMemoryType(uint32_t filter, VkMemoryPropertyFlags props)
{
    VkPhysicalDeviceMemoryProperties mp;
    vkGetPhysicalDeviceMemoryProperties(m_physicalDevice, &mp);
    for (uint32_t i = 0; i < mp.memoryTypeCount; ++i)
        if ((filter & (1u << i)) && (mp.memoryTypes[i].propertyFlags & props) == props)
            return i;
    return 0;
}

VkShaderModule VC::VulkanHeadlessRenderer::createShaderModule(const std::vector<uint32_t>& code)
{
    VkShaderModuleCreateInfo ci{};
    ci.sType = VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO;
    ci.codeSize = code.size() * sizeof(uint32_t);
    ci.pCode = code.data();
    VkShaderModule mod = VK_NULL_HANDLE;
    vkCreateShaderModule(m_device, &ci, nullptr, &mod);
    return mod;
}

void VC::VulkanHeadlessRenderer::transitionImageLayout(VkImage image, VkImageLayout from, VkImageLayout to)
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

        VkPipelineStageFlags srcStage, dstStage;
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

void VC::VulkanHeadlessRenderer::copyBufferToImage(VkBuffer buf, VkImage image, uint32_t w, uint32_t h)
{
    runOneShot(m_device, m_commandPool, m_graphicsQueue, [&](VkCommandBuffer cb) {
        VkBufferImageCopy region{};
        region.imageSubresource = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 0, 1};
        region.imageExtent = {w, h, 1};
        vkCmdCopyBufferToImage(cb, buf, image, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, 1, &region);
    });
}

void VC::VulkanHeadlessRenderer::updateUniforms()
{
    static auto start = std::chrono::high_resolution_clock::now();
    float       t = std::chrono::duration<float>(std::chrono::high_resolution_clock::now() - start).count();

    struct UBO
    {
        float time, pad[3], res[2], pixelSize, pad2;
    } ubo{};

    ubo.time = t;
    ubo.res[0] = (float)m_extent.width;
    ubo.res[1] = (float)m_extent.height;
    ubo.pixelSize = 1.f / (float)std::min(m_extent.width, m_extent.height);

    void* data;
    vkMapMemory(m_device, m_uniformMemory, 0, sizeof(ubo), 0, &data);
    memcpy(data, &ubo, sizeof(ubo));
    vkUnmapMemory(m_device, m_uniformMemory);
}

// ===========================================================================
// uploadTexture
// ===========================================================================

VkDescriptorSet VC::VulkanHeadlessRenderer::uploadTexture(const cv::Mat& mat)
{
    uint32_t     w = (uint32_t)mat.cols;
    uint32_t     h = (uint32_t)mat.rows;
    VkDeviceSize imageSize = (VkDeviceSize)(w * h * 4);

    VkBuffer       stagingBuf = VK_NULL_HANDLE;
    VkDeviceMemory stagingMem = VK_NULL_HANDLE;
    makeBuffer(m_device, imageSize, VK_BUFFER_USAGE_TRANSFER_SRC_BIT, stagingBuf, stagingMem, [this](uint32_t f, VkMemoryPropertyFlags p) { return findMemoryType(f, p); });

    void* data;
    vkMapMemory(m_device, stagingMem, 0, imageSize, 0, &data);
    std::memcpy(data, mat.data, (size_t)imageSize);
    vkUnmapMemory(m_device, stagingMem);

    TextureResource   tex{};
    VkImageCreateInfo ici{};
    ici.sType = VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO;
    ici.imageType = VK_IMAGE_TYPE_2D;
    ici.format = VK_FORMAT_B8G8R8A8_UNORM;
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

    transitionImageLayout(tex.image, VK_IMAGE_LAYOUT_UNDEFINED, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL);
    copyBufferToImage(stagingBuf, tex.image, w, h);
    transitionImageLayout(tex.image, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL);

    vkDestroyBuffer(m_device, stagingBuf, nullptr);
    vkFreeMemory(m_device, stagingMem, nullptr);

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

    VkDescriptorSetAllocateInfo dsAi{};
    dsAi.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO;
    dsAi.descriptorPool = m_texPool;
    dsAi.descriptorSetCount = 1;
    dsAi.pSetLayouts = &m_texLayout;
    VkDescriptorSet descSet = VK_NULL_HANDLE;
    vkAllocateDescriptorSets(m_device, &dsAi, &descSet);

    VkDescriptorImageInfo imgInfo{tex.sampler, tex.view, VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL};
    VkWriteDescriptorSet  dsW{};
    dsW.sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
    dsW.dstSet = descSet;
    dsW.dstBinding = 0;
    dsW.descriptorCount = 1;
    dsW.descriptorType = VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER;
    dsW.pImageInfo = &imgInfo;
    vkUpdateDescriptorSets(m_device, 1, &dsW, 0, nullptr);

    m_textureIndex[descSet] = m_textures.size();
    m_textures.push_back(tex);
    return descSet;
}

void VC::VulkanHeadlessRenderer::updateTexturePixels(VkDescriptorSet desc, const cv::Mat& mat)
{
    auto it = m_textureIndex.find(desc);
    if (it == m_textureIndex.end()) return;
    TextureResource& tex = m_textures[it->second];

    uint32_t     w = static_cast<uint32_t>(mat.cols);
    uint32_t     h = static_cast<uint32_t>(mat.rows);
    VkDeviceSize imageSize = static_cast<VkDeviceSize>(w * h * 4);

    auto fm = [this](uint32_t f, VkMemoryPropertyFlags p) { return findMemoryType(f, p); };

    VkBuffer       stagingBuf = VK_NULL_HANDLE;
    VkDeviceMemory stagingMem = VK_NULL_HANDLE;
    makeBuffer(m_device, imageSize, VK_BUFFER_USAGE_TRANSFER_SRC_BIT, stagingBuf, stagingMem, fm);

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

// ===========================================================================
// setMeshes
// ===========================================================================

void VC::VulkanHeadlessRenderer::setMeshes(const std::vector<Mesh>& meshes)
{
    m_vertices.clear();
    m_indices.clear();
    m_meshes = meshes;
    m_meshDrawInfos.clear();
    m_effectMeshIndices.clear();
    m_inputIndexToMeshPos.clear();
    m_matteSourceMeshPositions.clear();
    m_adjustmentMeshPositions.clear();

    // Map input index → mesh position first: a matte consumer references its
    // source by input index, but mesh order ≠ input order after filtering + the
    // zIndex sort, so we need identity to resolve it.
    for (size_t mi = 0; mi < meshes.size(); ++mi)
        if (meshes[mi].inputIndex >= 0)
            m_inputIndexToMeshPos[meshes[mi].inputIndex] = mi;

    // Mark which mesh positions are referenced as a matte source — those must
    // also be isolated (so their finished layer exists for the combine) and
    // excluded from the main draw loop (consumed only as a mask).
    for (const auto& mesh : meshes) {
        if (mesh.matteSourceInputIndex < 0) continue;
        auto it = m_inputIndexToMeshPos.find(mesh.matteSourceInputIndex);
        if (it != m_inputIndexToMeshPos.end())
            m_matteSourceMeshPositions.insert(it->second);
    }

    for (size_t mi = 0; mi < meshes.size(); ++mi) {
        const auto& mesh = meshes[mi];

        MeshDrawInfo info{};
        info.firstIndex = (uint32_t)m_indices.size();
        info.indexCount = (uint32_t)mesh.indices.size();

        uint32_t offset = (uint32_t)m_vertices.size();
        m_vertices.insert(m_vertices.end(), mesh.vertices.begin(), mesh.vertices.end());
        for (auto idx : mesh.indices)
            m_indices.push_back(offset + idx);
        m_meshDrawInfos.push_back(info);

        // Isolate meshes with a GLSL effect chain, matte consumers, matte
        // sources, AND adjustment layers. A zero-effect isolated mesh is fine:
        // the effect-chain loop Passthrough-flushes its seed render into its slot
        // when the effect list is empty (an effect-less adjustment layer thus
        // flattens-and-recomposites its below-range unchanged — an identity grade).
        if (!mesh.effects.empty() || mesh.matteSourceInputIndex >= 0 || m_matteSourceMeshPositions.count(mi) || mesh.isAdjustmentLayer)
            m_effectMeshIndices.push_back(mi);

        // Adjustment-layer chunk boundaries, collected in the already z-sorted
        // mesh order — so this vector is ascending with no extra sort.
        if (mesh.isAdjustmentLayer)
            m_adjustmentMeshPositions.push_back(mi);
    }

    // Object-space → absolute-UV param patching (Crop/Vignette bbox,
    // LightSweep group union) — shared with VulkanWidget, see EffectResolver.hpp.
    resolveEffectParams(m_meshes);

    m_geomDirty = true;

    if (!m_effectMeshIndices.empty())
        ensureEffectResultCapacity(m_effectMeshIndices.size());

    // One matte descriptor set per resolvable matte consumer this frame.
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

// ===========================================================================
// readFrame — render + readback
// ===========================================================================

cv::Mat VC::VulkanHeadlessRenderer::readFrame()
{
    cv::Mat result;

    // Pipelining: wait for the PREVIOUS submission to finish and copy its
    // pixels out now — this memcpy overlaps with the GPU work for the new
    // frame submitted below, instead of happening after a fresh vkQueueWaitIdle.
    if (m_hasPending) {
        vkWaitForFences(m_device, 1, &m_renderFence, VK_TRUE, UINT64_MAX);
        result = copyReadback(m_pendingIdx);
        vkResetFences(m_device, 1, &m_renderFence);
    }

    // The GPU is now idle (fence wait above, or this is the first call), so
    // it's safe to overwrite the shared single-instance resources below.
    updateUniforms();

    if (m_geomDirty) {
        auto upload = [&](VkDeviceMemory mem, const void* src, VkDeviceSize sz) {
            void* data;
            vkMapMemory(m_device, mem, 0, sz, 0, &data);
            memcpy(data, src, sz);
            vkUnmapMemory(m_device, mem);
        };
        if (!m_vertices.empty())
            upload(m_vertexMemory, m_vertices.data(), sizeof(Vertex) * m_vertices.size());
        if (!m_indices.empty())
            upload(m_indexMemory, m_indices.data(), sizeof(uint32_t) * m_indices.size());
        m_geomDirty = false;
    }

    size_t curIdx = m_hasPending ? 1 - m_pendingIdx : 0;

    vkResetCommandBuffer(m_commandBuffer, 0);

    VkCommandBufferBeginInfo bi{};
    bi.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO;
    vkBeginCommandBuffer(m_commandBuffer, &bi);

    // ── Effect pre-passes (render-to-texture + GLSL effect chain, per mesh) ──
    // Each effect-bearing mesh gets its own geometry pass + effect chain on
    // the shared ping/pong scratch images, finalized via the "Passthrough"
    // shader into its own dedicated result image (m_effectResults[slot]).
    // These results are composited in zIndex order in the main pass below,
    // instead of one global post-process pass.
    // Explicit pipeline barriers between passes are required for correct
    // synchronization on MoltenVK / Metal, which may not honour subpass
    // external dependencies reliably.
    // Running index into m_lutSets across ALL lut combines this frame — a
    // descriptor set can't be re-pointed mid-command-buffer, so each combine
    // (any mesh, any lut effect) needs its own set.
    size_t lutN = 0;

    // effect-mesh position → its result slot. Needed here (not just the main
    // pass) so an adjustment-layer flatten can composite chunk meshes' own
    // effect results and seed from a previous layer's graded result.
    std::unordered_map<size_t, size_t> effectSlotForMesh;
    for (size_t s = 0; s < m_effectMeshIndices.size(); ++s)
        effectSlotForMesh[m_effectMeshIndices[s]] = s;

    // Running index into m_adjustmentMeshPositions as we meet adjustment layers
    // in ascending slot order (m_effectMeshIndices is z-sorted, so ALs appear in
    // the same order as m_adjustmentMeshPositions).
    size_t alIdx = 0;

    for (size_t slot = 0; slot < m_effectMeshIndices.size(); ++slot) {
        size_t meshIdx = m_effectMeshIndices[slot];

        if (m_meshes[meshIdx].isAdjustmentLayer) {
            // Seed ping with the flattened composite of everything below this
            // layer. chunkBegin = just past the previous adjustment layer (or 0);
            // the layer mesh itself (meshIdx) is excluded (exclusive end). seedSlot
            // = the previous layer's result, so its grade is already baked in.
            size_t chunkBegin = (alIdx == 0) ? 0 : m_adjustmentMeshPositions[alIdx - 1] + 1;
            int    seedSlot   = (alIdx == 0) ? -1 : (int)effectSlotForMesh[m_adjustmentMeshPositions[alIdx - 1]];
            recordAdjustmentFlattenPass(m_commandBuffer, chunkBegin, meshIdx, seedSlot, effectSlotForMesh);
            ++alIdx;
        } else {
            recordEffectGeomPass(m_commandBuffer, m_pingFb, meshIdx);
        }
        // RAW: flatten/geom's write of ping → first effect pass read of ping
        effectBarrier(m_commandBuffer, VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT, VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT, m_pingImage, VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT, VK_ACCESS_SHADER_READ_BIT);

        // Track which scratch image holds the current result instead of
        // forcing it back into ping after every effect — running single-pass
        // effects a second time just to land in ping doubled their GPU cost
        // and double-applied non-idempotent ones (gamma² , 2× sweep intensity).
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
                recordEffectKernelPass(m_commandBuffer, dstFb, srcSet, eff.name, 1.f / m_extent.width, 0.f, eff.params);
                // RAW on dst + WAR on src (H wrote dst, read src; V reads dst, writes src)
                effectBarrier2(m_commandBuffer, dstImg, srcImg);

                recordEffectKernelPass(m_commandBuffer, srcFb, dstSet, eff.name, 0.f, 1.f / m_extent.height, eff.params);
                // RAW: V's write of src → next pass read of src
                effectBarrier(m_commandBuffer, VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT, VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT, srcImg, VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT, VK_ACCESS_SHADER_READ_BIT);
            } else if (lower == "glow") {
                // Glow/bloom (Strategy B — additive combine). This is the ONE
                // hand-built exception to the single-sampler / CLEAR-blend
                // effect-chain convention: it blurs a copy of the input and
                // additively composites that halo back onto the sharp original.
                // Both need the original to survive blur's in-place H/V passes,
                // so we stash it in the third scratch buffer first.
                //
                // params arrive ALPHABETICALLY → [intensity, radius]. radius
                // drives blur's sigma; intensity scales the additive halo.
                float              intensity = eff.params.empty() ? 1.f : eff.params[0];
                std::vector<float> blurParams = {eff.params.size() > 1 ? eff.params[1] : 5.f};

                // P1: preserve the sharp original into the third buffer.
                recordEffectKernelPass(m_commandBuffer, m_thirdFb, srcSet, "Passthrough", 0.f, 0.f, {});
                effectBarrier(m_commandBuffer, VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT, VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT, m_thirdImage, VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT, VK_ACCESS_SHADER_READ_BIT);

                // P2/P3: blur src in place (identical topology to the blur branch).
                recordEffectKernelPass(m_commandBuffer, dstFb, srcSet, "Blur", 1.f / m_extent.width, 0.f, blurParams);
                effectBarrier2(m_commandBuffer, dstImg, srcImg);
                recordEffectKernelPass(m_commandBuffer, srcFb, dstSet, "Blur", 0.f, 1.f / m_extent.height, blurParams);
                effectBarrier(m_commandBuffer, VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT, VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT, srcImg, VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT, VK_ACCESS_SHADER_READ_BIT);
                // Now: src = blurred, third = original, dst = stale (last read by P3).

                // P4: lay a fresh copy of the original into dst as the combine base.
                // WAR: P3 sampled dst — that read must finish before P4 clears+writes it.
                effectBarrier(m_commandBuffer, VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT, VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT, dstImg, VK_ACCESS_SHADER_READ_BIT, VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT);
                recordEffectKernelPass(m_commandBuffer, dstFb, m_thirdSrcSet, "Passthrough", 0.f, 0.f, {});
                // P4's colour write must be visible to P5's LOAD (read+write of dst).
                effectBarrier(m_commandBuffer, VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT, VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT, dstImg, VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT, VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT | VK_ACCESS_COLOR_ATTACHMENT_READ_BIT);

                // P5: additive combine. LOAD keeps dst's original; the (ONE,ONE)
                // blend adds intensity*blurred (sampled from src) on top.
                recordGlowCombinePass(m_commandBuffer, dstFb, srcSet, intensity);
                // Result now lives in dst — flip, same convention as the else branch.
                // RAW on dst (next reads it) + WAR on src (next may overwrite it).
                effectBarrier2(m_commandBuffer, dstImg, srcImg);
                inPing = !inPing;
            } else if (lower == "lut") {
                // LUT color grade — the THIRD hand-built exception (glow, matte
                // first). It samples a SECOND texture: a .cube atlas built ONCE
                // from eff.strParam (the file path) and cached across every
                // frame/mesh in m_lutCache (never re-parsed/re-uploaded). intensity
                // is the only numeric arg (p[0]); the atlas size rides separately.
                const LutResource* lr = eff.strParam.empty() ? nullptr : getOrBuildLut(eff.strParam);
                if (lr) {
                    float       intensity = eff.params.empty() ? 1.f : eff.params[0];
                    VkImageView srcView = inPing ? m_pingView : m_pongView;

                    // Point this combine's set at {content = current scratch,
                    // LUT atlas}. Safe to write in place: the GPU is idle here
                    // (fence waited at top of readFrame) and each combine owns
                    // its own set. binding 0 must match srcImg's live layout.
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

                    recordLutCombinePass(m_commandBuffer, dstFb, lutSet, intensity, (float)lr->size);
                    // RAW on dst (next pass reads it) + WAR on src (next may write it)
                    effectBarrier2(m_commandBuffer, dstImg, srcImg);
                    inPing = !inPing;
                }
                // LUT failed to load → skip silently, layer stays ungraded.
            } else {
                // Single pass: src → dst, result moves to dst. texelX/texelY
                // carry the real texel size here (Blur repurposes them as its
                // per-pass step direction above) — effects like Pixelate need
                // them to convert screen-pixel params into UV space.
                recordEffectKernelPass(m_commandBuffer, dstFb, srcSet, eff.name, 1.f / m_extent.width, 1.f / m_extent.height, eff.params);
                // RAW on dst (next pass reads it) + WAR on src (next pass may write it)
                effectBarrier2(m_commandBuffer, dstImg, srcImg);
                inPing = !inPing;
            }
        }

        // Flush the final result into this mesh's dedicated result image.
        recordEffectKernelPass(m_commandBuffer, m_effectResults[slot].framebuffer, inPing ? m_pingSrcSet : m_pongSrcSet, "Passthrough", 0.f, 0.f, {});
        effectBarrier(m_commandBuffer, VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT, VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT, m_effectResults[slot].image, VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT, VK_ACCESS_SHADER_READ_BIT);
    }

    // ── Matte combine phase (after Phase 1: every consumer AND source slot is
    // now populated) ──────────────────────────────────────────────────────────
    // For each matte consumer, sample its own slot (content) + its source's
    // slot (matte) through the 2-sampler pipeline into ping, then Passthrough
    // ping back into the consumer's own slot — overwriting it with the masked
    // result, which the main pass composites like any effect mesh.
    {
        std::unordered_map<size_t, size_t> meshPosToSlot;
        for (size_t s = 0; s < m_effectMeshIndices.size(); ++s)
            meshPosToSlot[m_effectMeshIndices[s]] = s;

        size_t matteN = 0; // running matte descriptor-set index
        for (size_t s = 0; s < m_effectMeshIndices.size(); ++s) {
            size_t      consumerPos = m_effectMeshIndices[s];
            const Mesh& mesh = m_meshes[consumerPos];
            if (mesh.matteSourceInputIndex < 0) continue;

            auto srcMeshIt = m_inputIndexToMeshPos.find(mesh.matteSourceInputIndex);
            if (srcMeshIt == m_inputIndexToMeshPos.end()) continue; // source hidden/absent → leave unmasked
            auto srcSlotIt = meshPosToSlot.find(srcMeshIt->second);
            if (srcSlotIt == meshPosToSlot.end()) continue;

            const EffectResultSlot& consumerSlot = m_effectResults[s];
            const EffectResultSlot& sourceSlot = m_effectResults[srcSlotIt->second];

            // Point this combine's descriptor set at {content, matte}. Safe to
            // update in place: the GPU is idle here (fence waited at top of
            // readFrame), and each combine owns its own set.
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

            // WAR: any prior read of ping must finish before the combine clears+writes it.
            effectBarrier(m_commandBuffer, VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT, VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT, m_pingImage, VK_ACCESS_SHADER_READ_BIT, VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT);
            recordMatteCombinePass(m_commandBuffer, m_pingFb, matteSet);
            // RAW on ping (Passthrough reads it) + WAR on consumer slot (combine
            // read it, Passthrough now overwrites it).
            effectBarrier2(m_commandBuffer, m_pingImage, consumerSlot.image);

            recordEffectKernelPass(m_commandBuffer, consumerSlot.framebuffer, m_pingSrcSet, "Passthrough", 0.f, 0.f, {});
            // RAW: consumer slot's masked result → main pass composite read.
            effectBarrier(m_commandBuffer, VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT, VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT, consumerSlot.image, VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT, VK_ACCESS_SHADER_READ_BIT);
        }
    }

    // ── Main SSAA render pass ─────────────────────────────────────────────
    // Opt-in transparent clear for alpha-preserving exports; opaque gray
    // otherwise (the historical default every golden was captured against).
    VkClearValue clearColor = m_transparentClear
                                  ? VkClearValue{{{0.f, 0.f, 0.f, 0.f}}}
                                  : VkClearValue{{{0.2f, 0.2f, 0.2f, 1.0f}}};
    VkViewport   vp{0, 0, (float)m_ssaaExtent.width, (float)m_ssaaExtent.height, 0, 1};
    VkRect2D     sc{{0, 0}, m_ssaaExtent};

    VkRenderPassBeginInfo rpi{};
    rpi.sType = VK_STRUCTURE_TYPE_RENDER_PASS_BEGIN_INFO;
    rpi.renderPass = m_renderPass;
    rpi.framebuffer = m_framebuffer;
    rpi.renderArea.extent = m_ssaaExtent;
    rpi.clearValueCount = 1;
    rpi.pClearValues = &clearColor;

    vkCmdBeginRenderPass(m_commandBuffer, &rpi, VK_SUBPASS_CONTENTS_INLINE);
    vkCmdSetViewport(m_commandBuffer, 0, 1, &vp);
    vkCmdSetScissor(m_commandBuffer, 0, 1, &sc);
    // set=0 (UBO) is bound once: it persists across pipeline binds since every
    // blend-mode pipeline shares m_pipelineLayout. The pipeline itself is bound
    // per mesh below, keyed on mesh.blendMode.
    vkCmdBindDescriptorSets(m_commandBuffer, VK_PIPELINE_BIND_POINT_GRAPHICS, m_pipelineLayout, 0, 1, &m_uboSet, 0, nullptr);

    // m_meshes is already zIndex/zOrderSeq-sorted (Core::generateMeshes), so a
    // single ordered pass — interleaving normal-mesh geometry with effect-mesh
    // composite quads — preserves correct draw order for both. effectSlotForMesh
    // was built above (shared with the adjustment-layer flatten passes).
    //
    // With adjustment layers present, everything at/below the topmost layer is
    // already baked (and graded) into that layer's result: composite it as one
    // fullscreen quad, then draw only the meshes ABOVE it here. drawStart = 0 and
    // no seed quad when there are no adjustment layers → byte-identical to before.
    size_t drawStart = 0;
    if (!m_adjustmentMeshPositions.empty()) {
        size_t lastAL = m_adjustmentMeshPositions.back();
        auto   it = effectSlotForMesh.find(lastAL);
        if (it != effectSlotForMesh.end())
            recordCompositeResultQuad(m_commandBuffer, m_pipelines[0], m_effectResults[it->second].descriptorSet);
        drawStart = lastAL + 1;
    }
    recordMeshRange(m_commandBuffer, drawStart, m_meshes.size(), effectSlotForMesh, m_pipelines);

    vkCmdEndRenderPass(m_commandBuffer);
    // SSAA is now VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL (render pass finalLayout).

    // ── Transition readback UNDEFINED → TRANSFER_DST ─────────────────────
    VkImageMemoryBarrier toReadDst{};
    toReadDst.sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER;
    toReadDst.srcAccessMask = 0;
    toReadDst.dstAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT;
    toReadDst.oldLayout = VK_IMAGE_LAYOUT_UNDEFINED;
    toReadDst.newLayout = VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL;
    toReadDst.srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
    toReadDst.dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
    toReadDst.image = m_readbackImages[curIdx];
    toReadDst.subresourceRange = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1};
    vkCmdPipelineBarrier(m_commandBuffer, VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT, 0, 0, nullptr, 0, nullptr, 1, &toReadDst);

    // ── Blit SSAA (4×) → readback (1×) ───────────────────────────────────
    VkImageBlit blit{};
    blit.srcSubresource = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 0, 1};
    blit.srcOffsets[1] = {(int32_t)m_ssaaExtent.width, (int32_t)m_ssaaExtent.height, 1};
    blit.dstSubresource = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 0, 1};
    blit.dstOffsets[1] = {(int32_t)m_extent.width, (int32_t)m_extent.height, 1};
    vkCmdBlitImage(m_commandBuffer, m_ssaaImage, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL, m_readbackImages[curIdx], VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, 1, &blit, VK_FILTER_LINEAR);

    // ── Transition readback TRANSFER_DST → GENERAL (host read) ───────────
    VkImageMemoryBarrier toGeneral{};
    toGeneral.sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER;
    toGeneral.srcAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT;
    toGeneral.dstAccessMask = VK_ACCESS_HOST_READ_BIT;
    toGeneral.oldLayout = VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL;
    toGeneral.newLayout = VK_IMAGE_LAYOUT_GENERAL;
    toGeneral.srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
    toGeneral.dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
    toGeneral.image = m_readbackImages[curIdx];
    toGeneral.subresourceRange = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1};
    vkCmdPipelineBarrier(m_commandBuffer, VK_PIPELINE_STAGE_TRANSFER_BIT, VK_PIPELINE_STAGE_HOST_BIT, 0, 0, nullptr, 0, nullptr, 1, &toGeneral);

    vkEndCommandBuffer(m_commandBuffer);

    VkSubmitInfo si{};
    si.sType = VK_STRUCTURE_TYPE_SUBMIT_INFO;
    si.commandBufferCount = 1;
    si.pCommandBuffers = &m_commandBuffer;
    vkQueueSubmit(m_graphicsQueue, 1, &si, m_renderFence);

    m_pendingIdx = curIdx;
    m_hasPending = true;

    // result holds the PREVIOUS frame's pixels (or is empty on the first call).
    return result;
}

cv::Mat VC::VulkanHeadlessRenderer::flush()
{
    if (!m_hasPending)
        return cv::Mat();

    vkWaitForFences(m_device, 1, &m_renderFence, VK_TRUE, UINT64_MAX);
    cv::Mat result = copyReadback(m_pendingIdx);
    vkResetFences(m_device, 1, &m_renderFence);
    m_hasPending = false;
    return result;
}

cv::Mat VC::VulkanHeadlessRenderer::copyReadback(size_t idx)
{
    VkImageSubresource  subRes{VK_IMAGE_ASPECT_COLOR_BIT, 0, 0};
    VkSubresourceLayout layout{};
    vkGetImageSubresourceLayout(m_device, m_readbackImages[idx], &subRes, &layout);

    void* mapped;
    vkMapMemory(m_device, m_readbackMemories[idx], 0, VK_WHOLE_SIZE, 0, &mapped);

    cv::Mat  result(m_extent.height, m_extent.width, CV_8UC4);
    uint8_t* src = static_cast<uint8_t*>(mapped) + layout.offset;
    for (uint32_t row = 0; row < m_extent.height; ++row)
        memcpy(result.ptr(row), src + row * layout.rowPitch, m_extent.width * 4);

    vkUnmapMemory(m_device, m_readbackMemories[idx]);
    return result;
}

// ===========================================================================
// createEffectResources — ping/pong images, effect render pass, pipelines
// ===========================================================================

static bool makeEffectImage(VkDevice device, VkPhysicalDevice /*physDev*/, uint32_t w, uint32_t h, VkImage& img, VkDeviceMemory& mem, VkImageView& view, std::function<uint32_t(uint32_t, VkMemoryPropertyFlags)> findMem)
{
    VkImageCreateInfo ici{};
    ici.sType = VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO;
    ici.imageType = VK_IMAGE_TYPE_2D;
    ici.format = VK_FORMAT_B8G8R8A8_UNORM;
    ici.extent = {w, h, 1};
    ici.mipLevels = 1;
    ici.arrayLayers = 1;
    ici.samples = VK_SAMPLE_COUNT_1_BIT;
    ici.tiling = VK_IMAGE_TILING_OPTIMAL;
    ici.usage = VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT | VK_IMAGE_USAGE_SAMPLED_BIT;
    ici.sharingMode = VK_SHARING_MODE_EXCLUSIVE;
    ici.initialLayout = VK_IMAGE_LAYOUT_UNDEFINED;
    if (vkCreateImage(device, &ici, nullptr, &img) != VK_SUCCESS) return false;

    VkMemoryRequirements req;
    vkGetImageMemoryRequirements(device, img, &req);
    VkMemoryAllocateInfo ai{};
    ai.sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
    ai.allocationSize = req.size;
    ai.memoryTypeIndex = findMem(req.memoryTypeBits, VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT);
    if (vkAllocateMemory(device, &ai, nullptr, &mem) != VK_SUCCESS) return false;
    vkBindImageMemory(device, img, mem, 0);

    VkImageViewCreateInfo ivci{};
    ivci.sType = VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO;
    ivci.image = img;
    ivci.viewType = VK_IMAGE_VIEW_TYPE_2D;
    ivci.format = VK_FORMAT_B8G8R8A8_UNORM;
    ivci.subresourceRange = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1};
    return vkCreateImageView(device, &ivci, nullptr, &view) == VK_SUCCESS;
}

bool VC::VulkanHeadlessRenderer::createEffectResources()
{
    auto fm = [this](uint32_t f, VkMemoryPropertyFlags p) { return findMemoryType(f, p); };

    // Ping/pong scratch images
    if (!makeEffectImage(m_device, m_physicalDevice, m_extent.width, m_extent.height, m_pingImage, m_pingMemory, m_pingView, fm)) return false;
    if (!makeEffectImage(m_device, m_physicalDevice, m_extent.width, m_extent.height, m_pongImage, m_pongMemory, m_pongView, fm)) return false;

    // Effect render pass: transparent clear, SHADER_READ_ONLY_OPTIMAL final
    {
        VkAttachmentDescription att{};
        att.format = VK_FORMAT_B8G8R8A8_UNORM;
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
        // RAW: colour-attachment writes must be visible to subsequent fragment-shader reads
        deps[0].srcSubpass = 0;
        deps[0].dstSubpass = VK_SUBPASS_EXTERNAL;
        deps[0].srcStageMask = VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT;
        deps[0].srcAccessMask = VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT;
        deps[0].dstStageMask = VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT;
        deps[0].dstAccessMask = VK_ACCESS_SHADER_READ_BIT;
        // WAR: preceding fragment-shader reads must complete before colour-attachment writes begin.
        // Without this, the V-blur pass's LOAD_OP_CLEAR can race with the H-blur pass still
        // sampling the ping image, producing non-deterministic blur output.
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
        if (vkCreateRenderPass(m_device, &rpci, nullptr, &m_effectPass) != VK_SUCCESS)
            return false;
    }

    // Framebuffers
    auto makeFb = [&](VkImageView view, VkFramebuffer& fb) -> bool {
        VkFramebufferCreateInfo fci{};
        fci.sType = VK_STRUCTURE_TYPE_FRAMEBUFFER_CREATE_INFO;
        fci.renderPass = m_effectPass;
        fci.attachmentCount = 1;
        fci.pAttachments = &view;
        fci.width = m_extent.width;
        fci.height = m_extent.height;
        fci.layers = 1;
        return vkCreateFramebuffer(m_device, &fci, nullptr, &fb) == VK_SUCCESS;
    };
    if (!makeFb(m_pingView, m_pingFb)) return false;
    if (!makeFb(m_pongView, m_pongFb)) return false;

    // Sampler for effect source images
    {
        VkSamplerCreateInfo sci{};
        sci.sType = VK_STRUCTURE_TYPE_SAMPLER_CREATE_INFO;
        sci.magFilter = VK_FILTER_LINEAR;
        sci.minFilter = VK_FILTER_LINEAR;
        sci.addressModeU = VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE;
        sci.addressModeV = VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE;
        sci.addressModeW = VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE;
        sci.maxLod = 0.f;
        if (vkCreateSampler(m_device, &sci, nullptr, &m_effectSampler) != VK_SUCCESS)
            return false;
    }

    // Allocate pingSrc, pongSrc (for effect pipeline set=0) and pingComp (main pipeline set=1)
    // All use m_texLayout (binding=0 = combined image sampler)
    auto allocAndWrite = [&](VkImageView view, VkDescriptorSet& set) -> bool {
        VkDescriptorSetAllocateInfo ai{};
        ai.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO;
        ai.descriptorPool = m_texPool;
        ai.descriptorSetCount = 1;
        ai.pSetLayouts = &m_texLayout;
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

    // Effect kernel pipelines — scan assets/shaders/*/frag.glsl automatically,
    // same auto-discovery as VulkanWidget (a hardcoded list here silently
    // dropped any newly added effect from the headless/--generate path).
    {
        std::filesystem::path shadersDir(std::string(SHADER_DIR));
        for (const auto& entry : std::filesystem::directory_iterator(shadersDir)) {
            if (!entry.is_directory()) continue;
            std::string dirName = entry.path().filename().string();
            // Skip non-effect dirs (geometry shaders, fullscreen quad vert).
            // "glow" is skipped too: its frag is the additive-combine half of a
            // hand-built two-stage pass, built separately by createGlowResources()
            // with blendEnable + a LOAD render pass — not a generic single-pass effect.
            // "matte" is skipped too: its frag samples TWO textures, so it needs
            // the hand-built 2-sampler layout/pipeline from createMatteResources(),
            // not the generic single-sampler auto-discovery path.
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

    // Static composite quad: fullscreen, mode=3 (textured), opacity=1
    {
        Vertex verts[4] = {
            {{-1.f, -1.f}, {0.f, 0.f}, {0.f, 0.f, 0.f, 1.f}, {3.f, 0.f, 0.f, 0.f}},
            {{1.f, -1.f}, {1.f, 0.f}, {0.f, 0.f, 0.f, 1.f}, {3.f, 0.f, 0.f, 0.f}},
            {{1.f, 1.f}, {1.f, 1.f}, {0.f, 0.f, 0.f, 1.f}, {3.f, 0.f, 0.f, 0.f}},
            {{-1.f, 1.f}, {0.f, 1.f}, {0.f, 0.f, 0.f, 1.f}, {3.f, 0.f, 0.f, 0.f}},
        };
        uint32_t idx[6] = {0, 1, 2, 0, 2, 3};

        auto uploadStatic = [&](const void* data, VkDeviceSize sz, VkBufferUsageFlags usage,
                                VkBuffer& buf, VkDeviceMemory& mem) -> bool {
            if (!makeBuffer(m_device, sz, usage, buf, mem, fm)) return false;
            void* mapped;
            vkMapMemory(m_device, mem, 0, sz, 0, &mapped);
            memcpy(mapped, data, sz);
            vkUnmapMemory(m_device, mem);
            return true;
        };

        if (!uploadStatic(verts, sizeof(verts), VK_BUFFER_USAGE_VERTEX_BUFFER_BIT, m_compVtxBuf, m_compVtxMem)) return false;
        if (!uploadStatic(idx, sizeof(idx), VK_BUFFER_USAGE_INDEX_BUFFER_BIT, m_compIdxBuf, m_compIdxMem)) return false;
    }

    return true;
}

// ===========================================================================
// ensureEffectResultCapacity — grow the per-effect-mesh result image pool
// ===========================================================================

bool VC::VulkanHeadlessRenderer::ensureEffectResultCapacity(size_t count)
{
    auto fm = [this](uint32_t f, VkMemoryPropertyFlags p) { return findMemoryType(f, p); };

    while (m_effectResults.size() < count) {
        EffectResultSlot slot{};

        if (!makeEffectImage(m_device, m_physicalDevice, m_extent.width, m_extent.height, slot.image, slot.memory, slot.view, fm))
            return false;

        VkFramebufferCreateInfo fci{};
        fci.sType = VK_STRUCTURE_TYPE_FRAMEBUFFER_CREATE_INFO;
        fci.renderPass = m_effectPass;
        fci.attachmentCount = 1;
        fci.pAttachments = &slot.view;
        fci.width = m_extent.width;
        fci.height = m_extent.height;
        fci.layers = 1;
        if (vkCreateFramebuffer(m_device, &fci, nullptr, &slot.framebuffer) != VK_SUCCESS)
            return false;

        VkDescriptorSetAllocateInfo ai{};
        ai.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO;
        ai.descriptorPool = m_texPool;
        ai.descriptorSetCount = 1;
        ai.pSetLayouts = &m_texLayout;
        if (vkAllocateDescriptorSets(m_device, &ai, &slot.descriptorSet) != VK_SUCCESS)
            return false;

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

bool VC::VulkanHeadlessRenderer::createEffectPipeline(const std::string& name)
{
    std::string lower = name;
    std::transform(lower.begin(), lower.end(), lower.begin(), ::tolower);

    auto vertSrc = loadEffectShader("effects", "vert.glsl");
    auto fragSrc = loadEffectShader(lower, "frag.glsl");
    if (vertSrc.empty() || fragSrc.empty()) return false; // GLSL not found — skip silently

    auto vertSpv = compileGLSL(vertSrc, VK_SHADER_STAGE_VERTEX_BIT);
    auto fragSpv = compileGLSL(fragSrc, VK_SHADER_STAGE_FRAGMENT_BIT);
    if (vertSpv.empty() || fragSpv.empty()) return false;

    // Pipeline layout: set=0 = sampler (reuse m_texLayout), push constants = EffectPC
    VkPushConstantRange pcRange{};
    pcRange.stageFlags = VK_SHADER_STAGE_FRAGMENT_BIT;
    pcRange.offset = 0;
    pcRange.size = sizeof(EffectPC);

    VkPipelineLayoutCreateInfo plci{};
    plci.sType = VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO;
    plci.setLayoutCount = 1;
    plci.pSetLayouts = &m_texLayout;
    plci.pushConstantRangeCount = 1;
    plci.pPushConstantRanges = &pcRange;

    EffectPipeline ep{};
    if (vkCreatePipelineLayout(m_device, &plci, nullptr, &ep.layout) != VK_SUCCESS)
        return false;

    VkShaderModule vert = createShaderModule(vertSpv);
    VkShaderModule frag = createShaderModule(fragSpv);

    VkPipelineShaderStageCreateInfo stages[2]{};
    stages[0] = {VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO, nullptr, 0, VK_SHADER_STAGE_VERTEX_BIT, vert, "main", nullptr};
    stages[1] = {VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO, nullptr, 0, VK_SHADER_STAGE_FRAGMENT_BIT, frag, "main", nullptr};

    // No vertex input — fullscreen quad driven by gl_VertexIndex
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

    // Replace-blend: effect writes are self-contained, no scene-layer blending needed here
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

    m_effectPipelines[lower] = ep;
    return true;
}

// ===========================================================================
// createGlowResources — glow-only extras (LOAD render pass, third scratch
// buffer, additive-combine pipeline). Kept out of the generic effect path
// because none of it fits the single-sampler / CLEAR / blend-disabled shape.
// ===========================================================================
bool VC::VulkanHeadlessRenderer::createGlowResources()
{
    auto fm = [this](uint32_t f, VkMemoryPropertyFlags p) { return findMemoryType(f, p); };

    // Third scratch buffer: holds the preserved sharp original across blur.
    if (!makeEffectImage(m_device, m_physicalDevice, m_extent.width, m_extent.height, m_thirdImage, m_thirdMemory, m_thirdView, fm)) return false;

    // LOAD render pass: identical to m_effectPass but loadOp = LOAD (keep the
    // existing contents) and initialLayout = SHADER_READ_ONLY_OPTIMAL (the
    // layout every effect image sits in between passes). Framebuffer
    // compatibility is by format/sample-count only, so it reuses the ping/pong
    // framebuffers built for m_effectPass — no new framebuffer needed here.
    {
        VkAttachmentDescription att{};
        att.format = VK_FORMAT_B8G8R8A8_UNORM;
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
        // The load reads the destination as a colour attachment, so the WAR/RAW
        // on it is against COLOR_ATTACHMENT_OUTPUT (not fragment reads).
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

    // Third framebuffer (built against m_effectPass — it's only ever a CLEAR target).
    {
        VkFramebufferCreateInfo fci{};
        fci.sType = VK_STRUCTURE_TYPE_FRAMEBUFFER_CREATE_INFO;
        fci.renderPass = m_effectPass;
        fci.attachmentCount = 1;
        fci.pAttachments = &m_thirdView;
        fci.width = m_extent.width;
        fci.height = m_extent.height;
        fci.layers = 1;
        if (vkCreateFramebuffer(m_device, &fci, nullptr, &m_thirdFb) != VK_SUCCESS) return false;
    }

    // Descriptor set reading the third buffer.
    {
        VkDescriptorSetAllocateInfo ai{};
        ai.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO;
        ai.descriptorPool = m_texPool;
        ai.descriptorSetCount = 1;
        ai.pSetLayouts = &m_texLayout;
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
    // into m_effectPassLoad. Same fullscreen-quad fixed-function state as the
    // generic effect pipelines — only the blend attachment and render pass differ.
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
        plci.pSetLayouts = &m_texLayout;
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

        // Additive: dst already holds the sharp original (LOAD), so out = original
        // + intensity*blurred. Alpha adds too, extending the halo's coverage.
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

// ===========================================================================
// createMatteResources — 2-sampler descriptor layout/pool + combine pipeline.
// The first 2-sampler descriptor set in the codebase; kept out of the generic
// effect path (which assumes a single sampler and a CLEAR/replace pipeline).
// ===========================================================================
bool VC::VulkanHeadlessRenderer::createMatteResources()
{
    // 2-binding layout: binding 0 = content (input A), binding 1 = matte (B).
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

    // Dedicated pool: 64 combine sets (2 samplers each). Kept separate from the
    // 128-slot texture pool so matte allocations don't compete with mesh textures.
    VkDescriptorPoolSize       ps{VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER, 128};
    VkDescriptorPoolCreateInfo pci{VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO};
    pci.maxSets = 64;
    pci.poolSizeCount = 1;
    pci.pPoolSizes = &ps;
    if (vkCreateDescriptorPool(m_device, &pci, nullptr, &m_mattePool) != VK_SUCCESS) return false;

    // Combine pipeline: fullscreen quad, CLEAR pass (m_effectPass), replace
    // blend (matte/frag.glsl writes final straight-alpha). No push constants.
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

bool VC::VulkanHeadlessRenderer::ensureMatteSetCapacity(size_t count)
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

void VC::VulkanHeadlessRenderer::recordMatteCombinePass(VkCommandBuffer cb, VkFramebuffer fb, VkDescriptorSet set)
{
    VkClearValue clear = {{{0.f, 0.f, 0.f, 0.f}}};
    VkViewport   vp{0, 0, (float)m_extent.width, (float)m_extent.height, 0, 1};
    VkRect2D     sc{{0, 0}, m_extent};

    VkRenderPassBeginInfo rpi{};
    rpi.sType = VK_STRUCTURE_TYPE_RENDER_PASS_BEGIN_INFO;
    rpi.renderPass = m_effectPass;
    rpi.framebuffer = fb;
    rpi.renderArea.extent = m_extent;
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

// ===========================================================================
// createLutResources — 2-sampler descriptor layout/pool + combine pipeline for
// the LUT color grade. Like matte but the pipeline layout carries push
// constants (intensity + atlas size). Kept out of the generic effect path.
// ===========================================================================
bool VC::VulkanHeadlessRenderer::createLutResources()
{
    // 2-binding layout: binding 0 = content, binding 1 = LUT atlas.
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

    // Combine pipeline: fullscreen quad, CLEAR pass (m_effectPass), replace
    // blend (lut/frag.glsl writes final straight-alpha), push constants = EffectPC.
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

const VC::VulkanHeadlessRenderer::LutResource* VC::VulkanHeadlessRenderer::getOrBuildLut(const std::string& filepath)
{
    auto it = m_lutCache.find(filepath);
    if (it != m_lutCache.end())
        return &it->second;

    cv::Mat atlas;
    int     N = 0;
    if (!parseCubeToAtlas(filepath, atlas, N)) {
        std::cerr << "LUT: failed to parse .cube '" << filepath << "'\n";
        return nullptr;
    }

    // Reuse the exact 2D-texture upload path Image/Video use: it stores the
    // TextureResource in m_textures (freed in cleanup) and returns its set. We
    // only need the atlas's view+sampler to bind into the 2-sampler LUT set.
    VkDescriptorSet ds = uploadTexture(atlas);
    const TextureResource& tex = m_textures[m_textureIndex[ds]];

    LutResource lr{tex.view, tex.sampler, N};
    auto [ins, _] = m_lutCache.emplace(filepath, lr);
    return &ins->second;
}

bool VC::VulkanHeadlessRenderer::ensureLutSetCapacity(size_t count)
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

void VC::VulkanHeadlessRenderer::recordLutCombinePass(VkCommandBuffer cb, VkFramebuffer fb, VkDescriptorSet set, float intensity, float lutSize)
{
    VkClearValue clear = {{{0.f, 0.f, 0.f, 0.f}}};
    VkViewport   vp{0, 0, (float)m_extent.width, (float)m_extent.height, 0, 1};
    VkRect2D     sc{{0, 0}, m_extent};

    VkRenderPassBeginInfo rpi{};
    rpi.sType = VK_STRUCTURE_TYPE_RENDER_PASS_BEGIN_INFO;
    rpi.renderPass = m_effectPass;
    rpi.framebuffer = fb;
    rpi.renderArea.extent = m_extent;
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

void VC::VulkanHeadlessRenderer::recordGlowCombinePass(VkCommandBuffer cb, VkFramebuffer fb, VkDescriptorSet srcSet, float intensity)
{
    // No clear value: LOAD render pass preserves the original already in `fb`.
    VkViewport vp{0, 0, (float)m_extent.width, (float)m_extent.height, 0, 1};
    VkRect2D   sc{{0, 0}, m_extent};

    VkRenderPassBeginInfo rpi{};
    rpi.sType = VK_STRUCTURE_TYPE_RENDER_PASS_BEGIN_INFO;
    rpi.renderPass = m_effectPassLoad;
    rpi.framebuffer = fb;
    rpi.renderArea.extent = m_extent;
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

void VC::VulkanHeadlessRenderer::recordEffectGeomPass(VkCommandBuffer cb, VkFramebuffer fb, size_t meshIndex)
{
    VkClearValue clear = {{{0.f, 0.f, 0.f, 0.f}}};
    VkViewport   vp{0, 0, (float)m_extent.width, (float)m_extent.height, 0, 1};
    VkRect2D     sc{{0, 0}, m_extent};

    VkRenderPassBeginInfo rpi{};
    rpi.sType = VK_STRUCTURE_TYPE_RENDER_PASS_BEGIN_INFO;
    rpi.renderPass = m_effectPass;
    rpi.framebuffer = fb;
    rpi.renderArea.extent = m_extent;
    rpi.clearValueCount = 1;
    rpi.pClearValues = &clear;

    vkCmdBeginRenderPass(cb, &rpi, VK_SUBPASS_CONTENTS_INLINE);
    vkCmdSetViewport(cb, 0, 1, &vp);
    vkCmdSetScissor(cb, 0, 1, &sc);

    // Reuse the Normal-mode geometry pipeline (same format + sample count as
    // m_effectPass): the isolated layer is always rendered onto a transparent
    // clear with standard alpha, then composited with its blend mode in the main pass.
    vkCmdBindPipeline(cb, VK_PIPELINE_BIND_POINT_GRAPHICS, m_pipelines[0]);
    vkCmdBindDescriptorSets(cb, VK_PIPELINE_BIND_POINT_GRAPHICS, m_pipelineLayout, 0, 1, &m_uboSet, 0, nullptr);

    VkDeviceSize zero = 0;
    vkCmdBindVertexBuffers(cb, 0, 1, &m_vertexBuffer, &zero);
    vkCmdBindIndexBuffer(cb, m_indexBuffer, 0, VK_INDEX_TYPE_UINT32);

    const Mesh&         mesh = m_meshes[meshIndex];
    const MeshDrawInfo& info = m_meshDrawInfos[meshIndex];
    if (mesh.hasTexture && mesh.textureDescriptor != VK_NULL_HANDLE) {
        vkCmdBindDescriptorSets(cb, VK_PIPELINE_BIND_POINT_GRAPHICS, m_pipelineLayout, 1, 1, &mesh.textureDescriptor, 0, nullptr);
    } else {
        vkCmdBindDescriptorSets(cb, VK_PIPELINE_BIND_POINT_GRAPHICS, m_pipelineLayout, 1, 1, &m_defaultTexSet, 0, nullptr);
    }
    vkCmdDrawIndexed(cb, info.indexCount, 1, info.firstIndex, 0, 0);

    vkCmdEndRenderPass(cb);
}

// ── Adjustment-layer support ───────────────────────────────────────────────
// recordMeshRange / recordCompositeResultQuad / recordAdjustmentFlattenPass are
// the fourth hand-built compositing exception (after glow, matte, LUT), and the
// first that operates on an arbitrary, order-sensitive COMPOSITE of many meshes
// rather than one/two isolated layers. recordMeshRange is the shared body of the
// main draw loop; the flatten pass reuses it to bake a below-range into ping,
// which the ordinary effect chain then grades — see readFrame().

void VC::VulkanHeadlessRenderer::recordMeshRange(
    VkCommandBuffer cb, size_t begin, size_t end,
    const std::unordered_map<size_t, size_t>& effectSlotForMesh,
    const VkPipeline* pipelines
)
{
    VkBuffer     vbufs[] = {m_vertexBuffer};
    VkDeviceSize offsets[] = {0};
    VkDeviceSize zero = 0;

    // Rebind the blend pipeline only on change — Normal-only ranges keep a
    // single bind. boundBlend starts fresh each call (a seed quad may already
    // have bound Normal, in which case the first mesh's Normal re-bind is elided
    // only if boundBlend were carried — it is not, so at most one extra bind).
    int boundBlend = -1;
    for (size_t mi = begin; mi < end; ++mi) {
        const Mesh& mesh = m_meshes[mi];

        // Matte sources are consumed only as a mask; adjustment layers are never
        // drawn directly (their grade reaches the screen via their result quad).
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
                vkCmdBindDescriptorSets(cb, VK_PIPELINE_BIND_POINT_GRAPHICS, m_pipelineLayout, 1, 1, &m_defaultTexSet, 0, nullptr);
            vkCmdDrawIndexed(cb, info.indexCount, 1, info.firstIndex, 0, 0);
        } else {
            // Composite this mesh's effect result as a full-resolution textured quad.
            // Transparent pixels are invisible; only the processed input is visible.
            vkCmdBindVertexBuffers(cb, 0, 1, &m_compVtxBuf, &zero);
            vkCmdBindIndexBuffer(cb, m_compIdxBuf, 0, VK_INDEX_TYPE_UINT32);
            vkCmdBindDescriptorSets(cb, VK_PIPELINE_BIND_POINT_GRAPHICS, m_pipelineLayout, 1, 1, &m_effectResults[effIt->second].descriptorSet, 0, nullptr);
            vkCmdDrawIndexed(cb, 6, 1, 0, 0, 0);
        }
    }
}

void VC::VulkanHeadlessRenderer::recordCompositeResultQuad(VkCommandBuffer cb, VkPipeline pipeline, VkDescriptorSet resultSet)
{
    VkDeviceSize zero = 0;
    vkCmdBindPipeline(cb, VK_PIPELINE_BIND_POINT_GRAPHICS, pipeline);
    vkCmdBindVertexBuffers(cb, 0, 1, &m_compVtxBuf, &zero);
    vkCmdBindIndexBuffer(cb, m_compIdxBuf, 0, VK_INDEX_TYPE_UINT32);
    vkCmdBindDescriptorSets(cb, VK_PIPELINE_BIND_POINT_GRAPHICS, m_pipelineLayout, 1, 1, &resultSet, 0, nullptr);
    vkCmdDrawIndexed(cb, 6, 1, 0, 0, 0);
}

void VC::VulkanHeadlessRenderer::recordAdjustmentFlattenPass(
    VkCommandBuffer cb, size_t begin, size_t end, int seedSlot,
    const std::unordered_map<size_t, size_t>& effectSlotForMesh
)
{
    // Transparent clear: the range flattens onto nothing, so its own alpha is
    // preserved and the graded result later composites over the real background
    // (same convention as every isolated effect layer).
    VkClearValue clear = {{{0.f, 0.f, 0.f, 0.f}}};
    VkViewport   vp{0, 0, (float)m_extent.width, (float)m_extent.height, 0, 1};
    VkRect2D     sc{{0, 0}, m_extent};

    VkRenderPassBeginInfo rpi{};
    rpi.sType = VK_STRUCTURE_TYPE_RENDER_PASS_BEGIN_INFO;
    rpi.renderPass = m_effectPass;
    rpi.framebuffer = m_pingFb;
    rpi.renderArea.extent = m_extent;
    rpi.clearValueCount = 1;
    rpi.pClearValues = &clear;

    vkCmdBeginRenderPass(cb, &rpi, VK_SUBPASS_CONTENTS_INLINE);
    vkCmdSetViewport(cb, 0, 1, &vp);
    vkCmdSetScissor(cb, 0, 1, &sc);
    // set=0 (UBO) shared across every blend pipeline via m_pipelineLayout.
    vkCmdBindDescriptorSets(cb, VK_PIPELINE_BIND_POINT_GRAPHICS, m_pipelineLayout, 0, 1, &m_uboSet, 0, nullptr);

    // Seed with the previous adjustment layer's graded result (everything below
    // it, already graded) so this chunk stacks on top of it. Normal blend over
    // the transparent clear makes the seed the base.
    if (seedSlot >= 0)
        recordCompositeResultQuad(cb, m_pipelines[0], m_effectResults[seedSlot].descriptorSet);

    // This chunk's own meshes on top, same per-mesh logic as the main pass. In
    // the headless renderer m_pipelines[] is format/sample-compatible with
    // m_effectPass (proven by recordEffectGeomPass reusing m_pipelines[0]), so we
    // reuse it directly — no separate blend-pipeline array is needed here (unlike
    // VulkanWidget, whose main pipelines are 4× MSAA and cannot bind in this pass).
    recordMeshRange(cb, begin, end, effectSlotForMesh, m_pipelines);

    vkCmdEndRenderPass(cb);
}

void VC::VulkanHeadlessRenderer::recordEffectKernelPass(
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
    VkViewport   vp{0, 0, (float)m_extent.width, (float)m_extent.height, 0, 1};
    VkRect2D     sc{{0, 0}, m_extent};

    VkRenderPassBeginInfo rpi{};
    rpi.sType = VK_STRUCTURE_TYPE_RENDER_PASS_BEGIN_INFO;
    rpi.renderPass = m_effectPass;
    rpi.framebuffer = fb;
    rpi.renderArea.extent = m_extent;
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

    vkCmdDraw(cb, 6, 1, 0, 0); // fullscreen quad from gl_VertexIndex, no vertex buffer
    vkCmdEndRenderPass(cb);
}

// ===========================================================================
// cleanup
// ===========================================================================

void VC::VulkanHeadlessRenderer::cleanup()
{
    if (!m_device) return;
    vkDeviceWaitIdle(m_device);

    if (m_renderFence) vkDestroyFence(m_device, m_renderFence, nullptr);
    vkDestroyCommandPool(m_device, m_commandPool, nullptr);
    vkDestroyFramebuffer(m_device, m_framebuffer, nullptr);

    if (m_ssaaImageView) vkDestroyImageView(m_device, m_ssaaImageView, nullptr);
    if (m_ssaaImage) vkDestroyImage(m_device, m_ssaaImage, nullptr);
    if (m_ssaaMemory) vkFreeMemory(m_device, m_ssaaMemory, nullptr);
    for (size_t i = 0; i < 2; ++i) {
        if (m_readbackImages[i]) vkDestroyImage(m_device, m_readbackImages[i], nullptr);
        if (m_readbackMemories[i]) vkFreeMemory(m_device, m_readbackMemories[i], nullptr);
    }

    for (VkPipeline& p : m_pipelines) {
        if (p != VK_NULL_HANDLE) vkDestroyPipeline(m_device, p, nullptr);
    }
    vkDestroyPipelineLayout(m_device, m_pipelineLayout, nullptr);
    vkDestroyRenderPass(m_device, m_renderPass, nullptr);

    for (auto& tex : m_textures) {
        vkDestroySampler(m_device, tex.sampler, nullptr);
        vkDestroyImageView(m_device, tex.view, nullptr);
        vkDestroyImage(m_device, tex.image, nullptr);
        vkFreeMemory(m_device, tex.memory, nullptr);
    }
    vkDestroySampler(m_device, m_defaultTexture.sampler, nullptr);
    vkDestroyImageView(m_device, m_defaultTexture.view, nullptr);
    vkDestroyImage(m_device, m_defaultTexture.image, nullptr);
    vkFreeMemory(m_device, m_defaultTexture.memory, nullptr);

    vkDestroyDescriptorPool(m_device, m_uboPool, nullptr);
    vkDestroyDescriptorPool(m_device, m_texPool, nullptr);
    vkDestroyDescriptorSetLayout(m_device, m_uboLayout, nullptr);
    vkDestroyDescriptorSetLayout(m_device, m_texLayout, nullptr);

    vkDestroyBuffer(m_device, m_uniformBuffer, nullptr);
    vkFreeMemory(m_device, m_uniformMemory, nullptr);
    vkDestroyBuffer(m_device, m_vertexBuffer, nullptr);
    vkFreeMemory(m_device, m_vertexMemory, nullptr);
    vkDestroyBuffer(m_device, m_indexBuffer, nullptr);
    vkFreeMemory(m_device, m_indexMemory, nullptr);

    // Effect resources
    for (auto& [name, ep] : m_effectPipelines) {
        vkDestroyPipeline(m_device, ep.pipeline, nullptr);
        vkDestroyPipelineLayout(m_device, ep.layout, nullptr);
    }
    // Glow-only extras
    if (m_glowCombine.pipeline) vkDestroyPipeline(m_device, m_glowCombine.pipeline, nullptr);
    if (m_glowCombine.layout) vkDestroyPipelineLayout(m_device, m_glowCombine.layout, nullptr);
    // Matte-only extras (sets freed with the pool)
    if (m_matteCombine.pipeline) vkDestroyPipeline(m_device, m_matteCombine.pipeline, nullptr);
    if (m_matteCombine.layout) vkDestroyPipelineLayout(m_device, m_matteCombine.layout, nullptr);
    if (m_mattePool) vkDestroyDescriptorPool(m_device, m_mattePool, nullptr);
    if (m_matteLayout) vkDestroyDescriptorSetLayout(m_device, m_matteLayout, nullptr);
    // LUT-only extras (sets freed with the pool; atlas images live in
    // m_textures, freed in the m_textures loop above).
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
    if (m_pingFb) vkDestroyFramebuffer(m_device, m_pingFb, nullptr);
    if (m_pongFb) vkDestroyFramebuffer(m_device, m_pongFb, nullptr);
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
    for (auto& slot : m_effectResults) {
        if (slot.framebuffer) vkDestroyFramebuffer(m_device, slot.framebuffer, nullptr);
        if (slot.view) vkDestroyImageView(m_device, slot.view, nullptr);
        if (slot.image) vkDestroyImage(m_device, slot.image, nullptr);
        if (slot.memory) vkFreeMemory(m_device, slot.memory, nullptr);
    }

    vkDestroyDevice(m_device, nullptr);
    vkDestroyInstance(m_instance, nullptr);
}
