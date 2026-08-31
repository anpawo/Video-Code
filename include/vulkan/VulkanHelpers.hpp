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
