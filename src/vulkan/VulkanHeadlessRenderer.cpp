/*
** EPITECH PROJECT, 2026
** video-code
** File description:
** VulkanHeadlessRenderer
*/

#include "vulkan/VulkanHeadlessRenderer.hpp"

#include <chrono>
#include <cstring>
#include <fstream>
#include <functional>
#include <iostream>
#include <sstream>

#include "vulkan/ShaderCompiler.hpp"

// ---------------------------------------------------------------------------
// loadShaderSource — read GLSL from assets/shaders/quadraticBezier/
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

// ---------------------------------------------------------------------------
// createBuffer helper (file-local, same as VulkanWidget.cpp)
// ---------------------------------------------------------------------------

static bool makeBuffer(
    VkDevice device, VkDeviceSize size, VkBufferUsageFlags usage,
    VkBuffer& outBuf, VkDeviceMemory& outMem,
    std::function<uint32_t(uint32_t, VkMemoryPropertyFlags)> findMem)
{
    VkBufferCreateInfo bi{};
    bi.sType       = VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO;
    bi.size        = size;
    bi.usage       = usage;
    bi.sharingMode = VK_SHARING_MODE_EXCLUSIVE;
    if (vkCreateBuffer(device, &bi, nullptr, &outBuf) != VK_SUCCESS) return false;

    VkMemoryRequirements req;
    vkGetBufferMemoryRequirements(device, outBuf, &req);

    VkMemoryAllocateInfo ai{};
    ai.sType           = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
    ai.allocationSize  = req.size;
    ai.memoryTypeIndex = findMem(req.memoryTypeBits,
        VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT);
    if (vkAllocateMemory(device, &ai, nullptr, &outMem) != VK_SUCCESS) return false;
    vkBindBufferMemory(device, outBuf, outMem, 0);
    return true;
}

// ---------------------------------------------------------------------------
// runOneShot helper — submit a command buffer and wait
// ---------------------------------------------------------------------------

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

// ===========================================================================
// Constructor / Destructor
// ===========================================================================

VC::VulkanHeadlessRenderer::VulkanHeadlessRenderer(uint32_t width, uint32_t height)
    : m_width(width)
    , m_height(height)
    , m_extent{width, height}
    , m_ssaaExtent{width * 4, height * 4}
{}

VC::VulkanHeadlessRenderer::~VulkanHeadlessRenderer()
{
    cleanup();
}

// ===========================================================================
// init — run all setup steps in order
// ===========================================================================

bool VC::VulkanHeadlessRenderer::init()
{
#define STEP(fn) if (!(fn)) { std::cerr << "VulkanHeadlessRenderer::init: " #fn " failed\n"; return false; }
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
    VkInstanceCreateFlags flags = 0;

    // On MoltenVK / macOS the portability enumeration extension is required
    // to enumerate physical devices, but only if it exists.
    if (hasExt("VK_KHR_portability_enumeration")) {
        extensions.push_back("VK_KHR_portability_enumeration");
        flags |= VK_INSTANCE_CREATE_ENUMERATE_PORTABILITY_BIT_KHR;
    }

    VkApplicationInfo appInfo{};
    appInfo.sType            = VK_STRUCTURE_TYPE_APPLICATION_INFO;
    appInfo.pApplicationName = "video-code-headless";
    appInfo.apiVersion       = VK_API_VERSION_1_0;

    VkInstanceCreateInfo ci{};
    ci.sType                   = VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO;
    ci.pApplicationInfo        = &appInfo;
    ci.enabledExtensionCount   = (uint32_t)extensions.size();
    ci.ppEnabledExtensionNames = extensions.data();
    ci.flags                   = flags;

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
    float priority = 1.0f;
    VkDeviceQueueCreateInfo qci{};
    qci.sType            = VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO;
    qci.queueFamilyIndex = m_graphicsFamily;
    qci.queueCount       = 1;
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
    ci.sType                   = VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO;
    ci.queueCreateInfoCount    = 1;
    ci.pQueueCreateInfos       = &qci;
    ci.enabledExtensionCount   = (uint32_t)extensions.size();
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
    ici.sType         = VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO;
    ici.imageType     = VK_IMAGE_TYPE_2D;
    ici.format        = VK_FORMAT_B8G8R8A8_UNORM;
    ici.extent        = {m_ssaaExtent.width, m_ssaaExtent.height, 1};
    ici.mipLevels     = 1;
    ici.arrayLayers   = 1;
    ici.samples       = VK_SAMPLE_COUNT_1_BIT;
    ici.tiling        = VK_IMAGE_TILING_OPTIMAL;
    ici.usage         = VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT | VK_IMAGE_USAGE_TRANSFER_SRC_BIT;
    ici.sharingMode   = VK_SHARING_MODE_EXCLUSIVE;
    ici.initialLayout = VK_IMAGE_LAYOUT_UNDEFINED;
    if (vkCreateImage(m_device, &ici, nullptr, &m_ssaaImage) != VK_SUCCESS) return false;

    VkMemoryRequirements memReq;
    vkGetImageMemoryRequirements(m_device, m_ssaaImage, &memReq);
    VkMemoryAllocateInfo ai{};
    ai.sType           = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
    ai.allocationSize  = memReq.size;
    ai.memoryTypeIndex = findMemoryType(memReq.memoryTypeBits, VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT);
    if (vkAllocateMemory(m_device, &ai, nullptr, &m_ssaaMemory) != VK_SUCCESS) return false;
    vkBindImageMemory(m_device, m_ssaaImage, m_ssaaMemory, 0);

    VkImageViewCreateInfo ivci{};
    ivci.sType            = VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO;
    ivci.image            = m_ssaaImage;
    ivci.viewType         = VK_IMAGE_VIEW_TYPE_2D;
    ivci.format           = VK_FORMAT_B8G8R8A8_UNORM;
    ivci.subresourceRange = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1};
    return vkCreateImageView(m_device, &ivci, nullptr, &m_ssaaImageView) == VK_SUCCESS;
}

// ===========================================================================
// Step 5: createReadbackResources — linear host-visible image at output size
// ===========================================================================

bool VC::VulkanHeadlessRenderer::createReadbackResources()
{
    VkImageCreateInfo ici{};
    ici.sType         = VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO;
    ici.imageType     = VK_IMAGE_TYPE_2D;
    ici.format        = VK_FORMAT_B8G8R8A8_UNORM;
    ici.extent        = {m_extent.width, m_extent.height, 1};
    ici.mipLevels     = 1;
    ici.arrayLayers   = 1;
    ici.samples       = VK_SAMPLE_COUNT_1_BIT;
    ici.tiling        = VK_IMAGE_TILING_LINEAR;
    ici.usage         = VK_IMAGE_USAGE_TRANSFER_DST_BIT;
    ici.sharingMode   = VK_SHARING_MODE_EXCLUSIVE;
    ici.initialLayout = VK_IMAGE_LAYOUT_UNDEFINED;
    if (vkCreateImage(m_device, &ici, nullptr, &m_readbackImage) != VK_SUCCESS) return false;

    VkMemoryRequirements memReq;
    vkGetImageMemoryRequirements(m_device, m_readbackImage, &memReq);
    VkMemoryAllocateInfo ai{};
    ai.sType           = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
    ai.allocationSize  = memReq.size;
    ai.memoryTypeIndex = findMemoryType(memReq.memoryTypeBits,
        VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT);
    if (vkAllocateMemory(m_device, &ai, nullptr, &m_readbackMemory) != VK_SUCCESS) return false;
    vkBindImageMemory(m_device, m_readbackImage, m_readbackMemory, 0);
    return true;
}

// ===========================================================================
// Step 6: createRenderPass
// ===========================================================================

bool VC::VulkanHeadlessRenderer::createRenderPass()
{
    VkAttachmentDescription col{};
    col.format         = VK_FORMAT_B8G8R8A8_UNORM;
    col.samples        = VK_SAMPLE_COUNT_1_BIT;
    col.loadOp         = VK_ATTACHMENT_LOAD_OP_CLEAR;
    col.storeOp        = VK_ATTACHMENT_STORE_OP_STORE;
    col.stencilLoadOp  = VK_ATTACHMENT_LOAD_OP_DONT_CARE;
    col.stencilStoreOp = VK_ATTACHMENT_STORE_OP_DONT_CARE;
    col.initialLayout  = VK_IMAGE_LAYOUT_UNDEFINED;
    col.finalLayout    = VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL;

    VkAttachmentReference ref{0, VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL};

    VkSubpassDescription subpass{};
    subpass.pipelineBindPoint    = VK_PIPELINE_BIND_POINT_GRAPHICS;
    subpass.colorAttachmentCount = 1;
    subpass.pColorAttachments    = &ref;

    VkSubpassDependency dep{};
    dep.srcSubpass    = VK_SUBPASS_EXTERNAL;
    dep.srcStageMask  = VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT;
    dep.dstStageMask  = VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT;
    dep.dstAccessMask = VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT;

    VkRenderPassCreateInfo ci{};
    ci.sType           = VK_STRUCTURE_TYPE_RENDER_PASS_CREATE_INFO;
    ci.attachmentCount = 1;
    ci.pAttachments    = &col;
    ci.subpassCount    = 1;
    ci.pSubpasses      = &subpass;
    ci.dependencyCount = 1;
    ci.pDependencies   = &dep;

    if (vkCreateRenderPass(m_device, &ci, nullptr, &m_renderPass) != VK_SUCCESS) return false;

    VkImageView             attachments[] = {m_ssaaImageView};
    VkFramebufferCreateInfo fci{};
    fci.sType           = VK_STRUCTURE_TYPE_FRAMEBUFFER_CREATE_INFO;
    fci.renderPass      = m_renderPass;
    fci.attachmentCount = 1;
    fci.pAttachments    = attachments;
    fci.width           = m_ssaaExtent.width;
    fci.height          = m_ssaaExtent.height;
    fci.layers          = 1;
    return vkCreateFramebuffer(m_device, &fci, nullptr, &m_framebuffer) == VK_SUCCESS;
}

// ===========================================================================
// Step 7: createUniformBuffer
// ===========================================================================

bool VC::VulkanHeadlessRenderer::createUniformBuffer()
{
    struct UBO { float time, pad[3], res[2], pixelSize, pad2; };
    return makeBuffer(m_device, sizeof(UBO), VK_BUFFER_USAGE_UNIFORM_BUFFER_BIT,
        m_uniformBuffer, m_uniformMemory,
        [this](uint32_t f, VkMemoryPropertyFlags p) { return findMemoryType(f, p); });
}

// ===========================================================================
// Step 8: createDescriptorSets — UBO (set=0) + texture pool (set=1)
// ===========================================================================

bool VC::VulkanHeadlessRenderer::createDescriptorSets()
{
    // set=0 UBO
    VkDescriptorSetLayoutBinding uboB{};
    uboB.binding         = 0;
    uboB.descriptorType  = VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER;
    uboB.descriptorCount = 1;
    uboB.stageFlags      = VK_SHADER_STAGE_FRAGMENT_BIT;
    VkDescriptorSetLayoutCreateInfo uboLci{VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO, nullptr, 0, 1, &uboB};
    vkCreateDescriptorSetLayout(m_device, &uboLci, nullptr, &m_uboLayout);

    VkDescriptorPoolSize uboPs{VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER, 1};
    VkDescriptorPoolCreateInfo uboPci{VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO, nullptr, 0, 1, 1, &uboPs};
    vkCreateDescriptorPool(m_device, &uboPci, nullptr, &m_uboPool);

    VkDescriptorSetAllocateInfo uboAi{VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO, nullptr, m_uboPool, 1, &m_uboLayout};
    vkAllocateDescriptorSets(m_device, &uboAi, &m_uboSet);

    struct UBO { float time, pad[3], res[2], pixelSize, pad2; };
    VkDescriptorBufferInfo bufInfo{m_uniformBuffer, 0, sizeof(UBO)};
    VkWriteDescriptorSet   uboW{VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET, nullptr,
        m_uboSet, 0, 0, 1, VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER, nullptr, &bufInfo, nullptr};
    vkUpdateDescriptorSets(m_device, 1, &uboW, 0, nullptr);

    // set=1 texture
    VkDescriptorSetLayoutBinding texB{};
    texB.binding         = 0;
    texB.descriptorType  = VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER;
    texB.descriptorCount = 1;
    texB.stageFlags      = VK_SHADER_STAGE_FRAGMENT_BIT;
    VkDescriptorSetLayoutCreateInfo texLci{VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO, nullptr, 0, 1, &texB};
    vkCreateDescriptorSetLayout(m_device, &texLci, nullptr, &m_texLayout);

    VkDescriptorPoolSize texPs{VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER, 64};
    VkDescriptorPoolCreateInfo texPci{VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO, nullptr,
        VK_DESCRIPTOR_POOL_CREATE_FREE_DESCRIPTOR_SET_BIT, 64, 1, &texPs};
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
    stages[0] = {VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO, nullptr, 0, VK_SHADER_STAGE_VERTEX_BIT,   vert, "main", nullptr};
    stages[1] = {VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO, nullptr, 0, VK_SHADER_STAGE_FRAGMENT_BIT, frag, "main", nullptr};

    VkVertexInputBindingDescription binding{0, sizeof(Vertex), VK_VERTEX_INPUT_RATE_VERTEX};
    VkVertexInputAttributeDescription attrs[4]{};
    attrs[0] = {0, 0, VK_FORMAT_R32G32_SFLOAT,          offsetof(Vertex, pos)};
    attrs[1] = {1, 0, VK_FORMAT_R32G32_SFLOAT,          offsetof(Vertex, uv)};
    attrs[2] = {2, 0, VK_FORMAT_R32G32B32A32_SFLOAT,    offsetof(Vertex, color)};
    attrs[3] = {3, 0, VK_FORMAT_R32G32B32A32_SFLOAT,    offsetof(Vertex, extra)};

    VkPipelineVertexInputStateCreateInfo vi{};
    vi.sType                            = VK_STRUCTURE_TYPE_PIPELINE_VERTEX_INPUT_STATE_CREATE_INFO;
    vi.vertexBindingDescriptionCount   = 1;
    vi.pVertexBindingDescriptions      = &binding;
    vi.vertexAttributeDescriptionCount = 4;
    vi.pVertexAttributeDescriptions    = attrs;

    VkPipelineInputAssemblyStateCreateInfo ia{};
    ia.sType    = VK_STRUCTURE_TYPE_PIPELINE_INPUT_ASSEMBLY_STATE_CREATE_INFO;
    ia.topology = VK_PRIMITIVE_TOPOLOGY_TRIANGLE_LIST;

    VkDynamicState dynStates[] = {VK_DYNAMIC_STATE_VIEWPORT, VK_DYNAMIC_STATE_SCISSOR};
    VkPipelineDynamicStateCreateInfo dyn{};
    dyn.sType             = VK_STRUCTURE_TYPE_PIPELINE_DYNAMIC_STATE_CREATE_INFO;
    dyn.dynamicStateCount = 2;
    dyn.pDynamicStates    = dynStates;

    VkPipelineViewportStateCreateInfo vs{};
    vs.sType         = VK_STRUCTURE_TYPE_PIPELINE_VIEWPORT_STATE_CREATE_INFO;
    vs.viewportCount = 1;
    vs.scissorCount  = 1;

    VkPipelineRasterizationStateCreateInfo rs{};
    rs.sType       = VK_STRUCTURE_TYPE_PIPELINE_RASTERIZATION_STATE_CREATE_INFO;
    rs.polygonMode = VK_POLYGON_MODE_FILL;
    rs.cullMode    = VK_CULL_MODE_NONE;
    rs.frontFace   = VK_FRONT_FACE_CLOCKWISE;
    rs.lineWidth   = 1.0f;

    VkPipelineMultisampleStateCreateInfo ms{};
    ms.sType                = VK_STRUCTURE_TYPE_PIPELINE_MULTISAMPLE_STATE_CREATE_INFO;
    ms.rasterizationSamples = VK_SAMPLE_COUNT_1_BIT;

    VkPipelineColorBlendAttachmentState blendA{};
    blendA.blendEnable         = VK_TRUE;
    blendA.srcColorBlendFactor = VK_BLEND_FACTOR_SRC_ALPHA;
    blendA.dstColorBlendFactor = VK_BLEND_FACTOR_ONE_MINUS_SRC_ALPHA;
    blendA.colorBlendOp        = VK_BLEND_OP_ADD;
    blendA.srcAlphaBlendFactor = VK_BLEND_FACTOR_ONE;
    blendA.dstAlphaBlendFactor = VK_BLEND_FACTOR_ONE_MINUS_SRC_ALPHA;
    blendA.alphaBlendOp        = VK_BLEND_OP_ADD;
    blendA.colorWriteMask      = VK_COLOR_COMPONENT_R_BIT | VK_COLOR_COMPONENT_G_BIT |
                                 VK_COLOR_COMPONENT_B_BIT | VK_COLOR_COMPONENT_A_BIT;

    VkPipelineColorBlendStateCreateInfo blend{};
    blend.sType           = VK_STRUCTURE_TYPE_PIPELINE_COLOR_BLEND_STATE_CREATE_INFO;
    blend.attachmentCount = 1;
    blend.pAttachments    = &blendA;

    VkPushConstantRange pcRange{VK_SHADER_STAGE_FRAGMENT_BIT, 0, 16};
    VkDescriptorSetLayout setLayouts[] = {m_uboLayout, m_texLayout};
    VkPipelineLayoutCreateInfo layoutCI{};
    layoutCI.sType                  = VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO;
    layoutCI.setLayoutCount         = 2;
    layoutCI.pSetLayouts            = setLayouts;
    layoutCI.pushConstantRangeCount = 1;
    layoutCI.pPushConstantRanges    = &pcRange;
    vkCreatePipelineLayout(m_device, &layoutCI, nullptr, &m_pipelineLayout);

    VkGraphicsPipelineCreateInfo ci{};
    ci.sType               = VK_STRUCTURE_TYPE_GRAPHICS_PIPELINE_CREATE_INFO;
    ci.stageCount          = 2;
    ci.pStages             = stages;
    ci.pVertexInputState   = &vi;
    ci.pInputAssemblyState = &ia;
    ci.pViewportState      = &vs;
    ci.pRasterizationState = &rs;
    ci.pMultisampleState   = &ms;
    ci.pColorBlendState    = &blend;
    ci.pDynamicState       = &dyn;
    ci.layout              = m_pipelineLayout;
    ci.renderPass          = m_renderPass;

    bool ok = vkCreateGraphicsPipelines(m_device, VK_NULL_HANDLE, 1, &ci, nullptr, &m_pipeline) == VK_SUCCESS;
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
    return makeBuffer(m_device, sizeof(Vertex) * 65536, VK_BUFFER_USAGE_VERTEX_BUFFER_BIT, m_vertexBuffer, m_vertexMemory, fm)
        && makeBuffer(m_device, sizeof(uint16_t) * 65536, VK_BUFFER_USAGE_INDEX_BUFFER_BIT, m_indexBuffer, m_indexMemory, fm);
}

// ===========================================================================
// Step 11 / 12: createCommandPool / createCommandBuffer
// ===========================================================================

bool VC::VulkanHeadlessRenderer::createCommandPool()
{
    VkCommandPoolCreateInfo ci{};
    ci.sType            = VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO;
    ci.flags            = VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT;
    ci.queueFamilyIndex = m_graphicsFamily;
    return vkCreateCommandPool(m_device, &ci, nullptr, &m_commandPool) == VK_SUCCESS;
}

bool VC::VulkanHeadlessRenderer::createCommandBuffer()
{
    VkCommandBufferAllocateInfo ai{};
    ai.sType              = VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO;
    ai.commandPool        = m_commandPool;
    ai.level              = VK_COMMAND_BUFFER_LEVEL_PRIMARY;
    ai.commandBufferCount = 1;
    return vkAllocateCommandBuffers(m_device, &ai, &m_commandBuffer) == VK_SUCCESS;
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
    ci.sType    = VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO;
    ci.codeSize = code.size() * sizeof(uint32_t);
    ci.pCode    = code.data();
    VkShaderModule mod = VK_NULL_HANDLE;
    vkCreateShaderModule(m_device, &ci, nullptr, &mod);
    return mod;
}

void VC::VulkanHeadlessRenderer::transitionImageLayout(VkImage image, VkImageLayout from, VkImageLayout to)
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
        region.imageExtent      = {w, h, 1};
        vkCmdCopyBufferToImage(cb, buf, image, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, 1, &region);
    });
}

void VC::VulkanHeadlessRenderer::updateUniforms()
{
    static auto start = std::chrono::high_resolution_clock::now();
    float t = std::chrono::duration<float>(std::chrono::high_resolution_clock::now() - start).count();

    struct UBO { float time, pad[3], res[2], pixelSize, pad2; } ubo{};
    ubo.time      = t;
    ubo.res[0]    = (float)m_extent.width;
    ubo.res[1]    = (float)m_extent.height;
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
    uint32_t     w         = (uint32_t)mat.cols;
    uint32_t     h         = (uint32_t)mat.rows;
    VkDeviceSize imageSize = (VkDeviceSize)(w * h * 4);

    VkBuffer       stagingBuf = VK_NULL_HANDLE;
    VkDeviceMemory stagingMem = VK_NULL_HANDLE;
    makeBuffer(m_device, imageSize, VK_BUFFER_USAGE_TRANSFER_SRC_BIT, stagingBuf, stagingMem,
        [this](uint32_t f, VkMemoryPropertyFlags p) { return findMemoryType(f, p); });

    void* data;
    vkMapMemory(m_device, stagingMem, 0, imageSize, 0, &data);
    std::memcpy(data, mat.data, (size_t)imageSize);
    vkUnmapMemory(m_device, stagingMem);

    TextureResource tex{};
    VkImageCreateInfo ici{};
    ici.sType         = VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO;
    ici.imageType     = VK_IMAGE_TYPE_2D;
    ici.format        = VK_FORMAT_B8G8R8A8_UNORM;
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

    transitionImageLayout(tex.image, VK_IMAGE_LAYOUT_UNDEFINED, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL);
    copyBufferToImage(stagingBuf, tex.image, w, h);
    transitionImageLayout(tex.image, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL);

    vkDestroyBuffer(m_device, stagingBuf, nullptr);
    vkFreeMemory(m_device, stagingMem, nullptr);

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

    VkDescriptorSetAllocateInfo dsAi{};
    dsAi.sType              = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO;
    dsAi.descriptorPool     = m_texPool;
    dsAi.descriptorSetCount = 1;
    dsAi.pSetLayouts        = &m_texLayout;
    VkDescriptorSet descSet = VK_NULL_HANDLE;
    vkAllocateDescriptorSets(m_device, &dsAi, &descSet);

    VkDescriptorImageInfo imgInfo{tex.sampler, tex.view, VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL};
    VkWriteDescriptorSet  dsW{};
    dsW.sType           = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
    dsW.dstSet          = descSet;
    dsW.dstBinding      = 0;
    dsW.descriptorCount = 1;
    dsW.descriptorType  = VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER;
    dsW.pImageInfo      = &imgInfo;
    vkUpdateDescriptorSets(m_device, 1, &dsW, 0, nullptr);

    m_textures.push_back(tex);
    return descSet;
}

// ===========================================================================
// setMeshes
// ===========================================================================

void VC::VulkanHeadlessRenderer::setMeshes(const std::vector<Mesh>& meshes)
{
    m_vertices.clear();
    m_indices.clear();
    m_meshes    = meshes;
    m_meshDrawInfos.clear();

    for (const auto& mesh : meshes) {
        MeshDrawInfo info{};
        info.firstIndex = (uint32_t)m_indices.size();
        info.indexCount = (uint32_t)mesh.indices.size();

        uint16_t offset = (uint16_t)m_vertices.size();
        m_vertices.insert(m_vertices.end(), mesh.vertices.begin(), mesh.vertices.end());
        for (auto idx : mesh.indices)
            m_indices.push_back(offset + idx);
        m_meshDrawInfos.push_back(info);
    }
    m_geomDirty = true;
}

// ===========================================================================
// readFrame — render + readback
// ===========================================================================

cv::Mat VC::VulkanHeadlessRenderer::readFrame()
{
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
            upload(m_indexMemory, m_indices.data(), sizeof(uint16_t) * m_indices.size());
        m_geomDirty = false;
    }

    vkResetCommandBuffer(m_commandBuffer, 0);

    VkCommandBufferBeginInfo bi{};
    bi.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO;
    vkBeginCommandBuffer(m_commandBuffer, &bi);

    // ── Render pass → SSAA image ──────────────────────────────────────────
    VkClearValue clearColor = {{{0.2f, 0.2f, 0.2f, 1.0f}}};
    VkViewport   vp{0, 0, (float)m_ssaaExtent.width, (float)m_ssaaExtent.height, 0, 1};
    VkRect2D     sc{{0, 0}, m_ssaaExtent};

    VkRenderPassBeginInfo rpi{};
    rpi.sType             = VK_STRUCTURE_TYPE_RENDER_PASS_BEGIN_INFO;
    rpi.renderPass        = m_renderPass;
    rpi.framebuffer       = m_framebuffer;
    rpi.renderArea.extent = m_ssaaExtent;
    rpi.clearValueCount   = 1;
    rpi.pClearValues      = &clearColor;

    vkCmdBeginRenderPass(m_commandBuffer, &rpi, VK_SUBPASS_CONTENTS_INLINE);
    vkCmdSetViewport(m_commandBuffer, 0, 1, &vp);
    vkCmdSetScissor(m_commandBuffer, 0, 1, &sc);
    vkCmdBindPipeline(m_commandBuffer, VK_PIPELINE_BIND_POINT_GRAPHICS, m_pipeline);
    vkCmdBindDescriptorSets(m_commandBuffer, VK_PIPELINE_BIND_POINT_GRAPHICS, m_pipelineLayout, 0, 1, &m_uboSet, 0, nullptr);

    VkBuffer     vbufs[] = {m_vertexBuffer};
    VkDeviceSize offsets[] = {0};
    vkCmdBindVertexBuffers(m_commandBuffer, 0, 1, vbufs, offsets);

    if (!m_indices.empty()) {
        vkCmdBindIndexBuffer(m_commandBuffer, m_indexBuffer, 0, VK_INDEX_TYPE_UINT16);
        vkCmdBindDescriptorSets(m_commandBuffer, VK_PIPELINE_BIND_POINT_GRAPHICS, m_pipelineLayout, 1, 1, &m_defaultTexSet, 0, nullptr);

        for (size_t i = 0; i < m_meshes.size(); ++i) {
            const Mesh&         mesh = m_meshes[i];
            const MeshDrawInfo& info = m_meshDrawInfos[i];
            if (mesh.hasTexture && mesh.textureDescriptor != VK_NULL_HANDLE) {
                vkCmdBindDescriptorSets(m_commandBuffer, VK_PIPELINE_BIND_POINT_GRAPHICS, m_pipelineLayout, 1, 1, &mesh.textureDescriptor, 0, nullptr);
            } else {
                vkCmdBindDescriptorSets(m_commandBuffer, VK_PIPELINE_BIND_POINT_GRAPHICS, m_pipelineLayout, 1, 1, &m_defaultTexSet, 0, nullptr);
            }
            if (!mesh.pushConstantData.empty()) {
                vkCmdPushConstants(m_commandBuffer, m_pipelineLayout, VK_SHADER_STAGE_FRAGMENT_BIT,
                    0, (uint32_t)mesh.pushConstantData.size(), mesh.pushConstantData.data());
            }
            vkCmdDrawIndexed(m_commandBuffer, info.indexCount, 1, info.firstIndex, 0, 0);
        }
    }
    vkCmdEndRenderPass(m_commandBuffer);
    // SSAA is now VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL (render pass finalLayout).

    // ── Transition readback UNDEFINED → TRANSFER_DST ─────────────────────
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

    // ── Blit SSAA (4×) → readback (1×) ───────────────────────────────────
    VkImageBlit blit{};
    blit.srcSubresource = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 0, 1};
    blit.srcOffsets[1]  = {(int32_t)m_ssaaExtent.width, (int32_t)m_ssaaExtent.height, 1};
    blit.dstSubresource = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 0, 1};
    blit.dstOffsets[1]  = {(int32_t)m_extent.width,    (int32_t)m_extent.height,    1};
    vkCmdBlitImage(m_commandBuffer,
        m_ssaaImage,    VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,
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

    VkSubmitInfo si{};
    si.sType              = VK_STRUCTURE_TYPE_SUBMIT_INFO;
    si.commandBufferCount = 1;
    si.pCommandBuffers    = &m_commandBuffer;
    vkQueueSubmit(m_graphicsQueue, 1, &si, VK_NULL_HANDLE);
    vkQueueWaitIdle(m_graphicsQueue);

    // ── Map and copy to cv::Mat ───────────────────────────────────────────
    VkImageSubresource  subRes{VK_IMAGE_ASPECT_COLOR_BIT, 0, 0};
    VkSubresourceLayout layout{};
    vkGetImageSubresourceLayout(m_device, m_readbackImage, &subRes, &layout);

    void* mapped;
    vkMapMemory(m_device, m_readbackMemory, 0, VK_WHOLE_SIZE, 0, &mapped);

    cv::Mat    result(m_extent.height, m_extent.width, CV_8UC4);
    uint8_t*   src = static_cast<uint8_t*>(mapped) + layout.offset;
    for (uint32_t row = 0; row < m_extent.height; ++row)
        memcpy(result.ptr(row), src + row * layout.rowPitch, m_extent.width * 4);

    vkUnmapMemory(m_device, m_readbackMemory);
    return result;
}

// ===========================================================================
// cleanup
// ===========================================================================

void VC::VulkanHeadlessRenderer::cleanup()
{
    if (!m_device) return;
    vkDeviceWaitIdle(m_device);

    vkDestroyCommandPool(m_device, m_commandPool, nullptr);
    vkDestroyFramebuffer(m_device, m_framebuffer, nullptr);

    if (m_ssaaImageView) vkDestroyImageView(m_device, m_ssaaImageView, nullptr);
    if (m_ssaaImage)     vkDestroyImage(m_device, m_ssaaImage, nullptr);
    if (m_ssaaMemory)    vkFreeMemory(m_device, m_ssaaMemory, nullptr);
    if (m_readbackImage)  vkDestroyImage(m_device, m_readbackImage, nullptr);
    if (m_readbackMemory) vkFreeMemory(m_device, m_readbackMemory, nullptr);

    vkDestroyPipeline(m_device, m_pipeline, nullptr);
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

    vkDestroyDevice(m_device, nullptr);
    vkDestroyInstance(m_instance, nullptr);
}
