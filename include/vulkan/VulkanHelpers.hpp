/*
** EPITECH PROJECT, 2026
** video-code
** File description:
** VulkanHelpers
*/

#pragma once

// The four helpers the two renderers had written out identically, character for
// character. They were `static` in each .cpp, so neither the compiler nor a
// reader could say so: the only way to notice was to diff two files nobody
// diffs. They are device-free by construction — every handle they touch arrives
// as an argument — which is what makes them the first safe thing to share, and
// what lets the 87 goldens cover both callers of each one at once.

#include <vulkan/vulkan.h>

#include <algorithm>
#include <fstream>
#include <functional>
#include <sstream>
#include <string>
#include <vector>

#include "vulkan/ShaderCompiler.hpp"

// Explicit image memory barrier between effect passes.
// More reliable than subpass external dependencies on MoltenVK / Metal.
inline void effectBarrier(VkCommandBuffer cb, VkPipelineStageFlags srcStage, VkPipelineStageFlags dstStage, VkImage image, VkAccessFlags srcAccess, VkAccessFlags dstAccess, VkImageLayout oldLayout = VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL, VkImageLayout newLayout = VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL)
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

// ---------------------------------------------------------------------------
// runOneShot helper — submit a command buffer and wait
// ---------------------------------------------------------------------------

inline void runOneShot(VkDevice device, VkCommandPool pool, VkQueue queue, const std::function<void(VkCommandBuffer)>& fn)
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

inline std::string loadEffectShader(const std::string& folder, const std::string& file)
{
    std::string   path = std::string(SHADER_DIR) + "/" + folder + "/" + file;
    std::ifstream f(path);
    if (!f.is_open()) return {};
    std::ostringstream ss;
    ss << f.rdbuf();
    return ss.str();
}

// Cache key for a runtime-loaded MathShader pipeline. Namespaced so a user
// file can never collide with an auto-discovered assets/shaders/ folder name,
// and pre-lowercased because recordEffectKernelPass lowercases its name before
// the m_effectPipelines lookup (the file itself is read with the original-case
// path — only the KEY is transformed, so insert and lookup always agree).
inline std::string mathPipelineKey(const std::string& path)
{
    std::string key = "math:" + path;
    std::transform(key.begin(), key.end(), key.begin(), ::tolower);
    return key;
}

namespace VC
{
    // ---------------------------------------------------------------------
    // The bodies both renderers wrote out identically. Each takes the handles
    // it needs rather than reading a member, so the class keeps the method its
    // call sites already use and that method keeps one line.
    // ---------------------------------------------------------------------

    inline VkShaderModule makeShaderModule(VkDevice device, const std::vector<uint32_t>& code)
    {
        VkShaderModuleCreateInfo ci{};
        ci.sType = VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO;
        ci.codeSize = code.size() * sizeof(uint32_t);
        ci.pCode = code.data();
        VkShaderModule mod = VK_NULL_HANDLE;
        vkCreateShaderModule(device, &ci, nullptr, &mod);
        return mod;
    }

    inline bool makeCommandPool(VkDevice device, uint32_t graphicsFamily, VkCommandPool& out)
    {
        VkCommandPoolCreateInfo ci{};
        ci.sType = VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO;
        ci.flags = VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT;
        ci.queueFamilyIndex = graphicsFamily;
        return vkCreateCommandPool(device, &ci, nullptr, &out) == VK_SUCCESS;
    }

    inline void copyBufferToImage(VkDevice device, VkCommandPool pool, VkQueue queue, VkBuffer buf, VkImage image, uint32_t w, uint32_t h)
    {
        runOneShot(device, pool, queue, [&](VkCommandBuffer cb) {
            VkBufferImageCopy region{};
            region.imageSubresource = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 0, 1};
            region.imageExtent = {w, h, 1};
            vkCmdCopyBufferToImage(cb, buf, image, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, 1, &region);
        });
    }

    inline void recordCompositeResultQuad(VkCommandBuffer cb, VkPipeline pipeline, VkPipelineLayout layout, VkBuffer vtx, VkBuffer idx, VkDescriptorSet resultSet)
    {
        VkDeviceSize zero = 0;
        vkCmdBindPipeline(cb, VK_PIPELINE_BIND_POINT_GRAPHICS, pipeline);
        vkCmdBindVertexBuffers(cb, 0, 1, &vtx, &zero);
        vkCmdBindIndexBuffer(cb, idx, 0, VK_INDEX_TYPE_UINT32);
        vkCmdBindDescriptorSets(cb, VK_PIPELINE_BIND_POINT_GRAPHICS, layout, 1, 1, &resultSet, 0, nullptr);
        vkCmdDrawIndexed(cb, 6, 1, 0, 0, 0);
    }

    // One function for what was four: the LUT and the matte allocate their
    // descriptor sets the same way, and each renderer had written both.
    inline bool ensureSetCapacity(VkDevice device, VkDescriptorPool pool, VkDescriptorSetLayout layout, std::vector<VkDescriptorSet>& sets, size_t count)
    {
        while (sets.size() < count) {
            VkDescriptorSet             set = VK_NULL_HANDLE;
            VkDescriptorSetAllocateInfo ai{VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO};
            ai.descriptorPool = pool;
            ai.descriptorSetCount = 1;
            ai.pSetLayouts = &layout;
            if (vkAllocateDescriptorSets(device, &ai, &set) != VK_SUCCESS) return false;
            sets.push_back(set);
        }
        return true;
    }

    // ---------------------------------------------------------------------
    // The LUT combine pass and the matte combine pass, which are one function.
    //
    // Each renderer had written both, so this body existed FOUR times: 410
    // lines saying the same thing, differing only in which folder the fragment
    // shader comes from and whether the pipeline takes push constants (the LUT
    // reads EffectPC, the matte reads none). Two of the four could never be
    // exercised by a test, since VulkanWidget needs a native window.
    // ---------------------------------------------------------------------
    inline bool createCombineResources(VkDevice device, VkRenderPass effectPass, const char* shaderFolder, uint32_t pushConstantSize, VkDescriptorSetLayout& outSetLayout, VkDescriptorPool& outPool, VkPipelineLayout& outPipelineLayout, VkPipeline& outPipeline)
    {
        // 2-binding layout: binding 0 = content, binding 1 = the atlas or the
        // matte source.
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
        if (vkCreateDescriptorSetLayout(device, &lci, nullptr, &outSetLayout) != VK_SUCCESS) return false;

        // Dedicated pool: 64 combine sets of 2 samplers, kept away from the
        // 128-slot texture pool so these never compete with mesh textures.
        VkDescriptorPoolSize       ps{VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER, 128};
        VkDescriptorPoolCreateInfo pci{VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO};
        pci.maxSets = 64;
        pci.poolSizeCount = 1;
        pci.pPoolSizes = &ps;
        if (vkCreateDescriptorPool(device, &pci, nullptr, &outPool) != VK_SUCCESS) return false;

        // Fullscreen quad, CLEAR pass, replace blend — the fragment shader
        // writes final straight-alpha.
        auto vertSrc = loadEffectShader("effects", "vert.glsl");
        auto fragSrc = loadEffectShader(shaderFolder, "frag.glsl");
        if (vertSrc.empty() || fragSrc.empty()) return false;
        auto vertSpv = compileGLSL(vertSrc, VK_SHADER_STAGE_VERTEX_BIT);
        auto fragSpv = compileGLSL(fragSrc, VK_SHADER_STAGE_FRAGMENT_BIT);
        if (vertSpv.empty() || fragSpv.empty()) return false;

        VkPushConstantRange pcRange{};
        pcRange.stageFlags = VK_SHADER_STAGE_FRAGMENT_BIT;
        pcRange.offset = 0;
        pcRange.size = pushConstantSize;

        VkPipelineLayoutCreateInfo plci{VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO};
        plci.setLayoutCount = 1;
        plci.pSetLayouts = &outSetLayout;
        plci.pushConstantRangeCount = pushConstantSize > 0 ? 1 : 0;
        plci.pPushConstantRanges = pushConstantSize > 0 ? &pcRange : nullptr;
        if (vkCreatePipelineLayout(device, &plci, nullptr, &outPipelineLayout) != VK_SUCCESS) return false;

        VkShaderModule vert = makeShaderModule(device, vertSpv);
        VkShaderModule frag = makeShaderModule(device, fragSpv);

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
        gpci.layout = outPipelineLayout;
        gpci.renderPass = effectPass;

        bool ok = vkCreateGraphicsPipelines(device, VK_NULL_HANDLE, 1, &gpci, nullptr, &outPipeline) == VK_SUCCESS;
        vkDestroyShaderModule(device, vert, nullptr);
        vkDestroyShaderModule(device, frag, nullptr);
        if (!ok) {
            vkDestroyPipelineLayout(device, outPipelineLayout, nullptr);
            outPipelineLayout = VK_NULL_HANDLE;
            return false;
        }
        return true;
    }
}
