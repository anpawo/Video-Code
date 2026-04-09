/*
** EPITECH PROJECT, 2026
** video-code
** File description:
** VulkanHeadlessRenderer — pure offscreen Vulkan renderer (no window, no swapchain)
*/

#pragma once

#include <vulkan/vulkan.h>
#include <opencv2/core/mat.hpp>
#include <vector>

#include "vulkan/Mesh.hpp"

namespace VC
{
    // -------------------------------------------------------------------------
    // VulkanHeadlessRenderer
    //   Initialises Vulkan without a surface or swapchain.
    //   Renders to a 4× SSAA offscreen image, blits down to a linear host-visible
    //   readback image, and returns the pixels as a cv::Mat (BGRA, CV_8UC4).
    //   Used by Compiler::generateVideo() — no Qt, no window, no event loop.
    // -------------------------------------------------------------------------
    class VulkanHeadlessRenderer
    {
    public:

        VulkanHeadlessRenderer(uint32_t width, uint32_t height);
        ~VulkanHeadlessRenderer();

        bool init();

        // Upload a BGRA cv::Mat to the GPU as a combined image sampler (set=1).
        VkDescriptorSet uploadTexture(const cv::Mat& mat);

        // Replace the scene geometry for the next readFrame() call.
        void setMeshes(const std::vector<Mesh>& meshes);

        // Render the current scene and return pixels as a BGRA cv::Mat.
        // Blocks until the GPU is done.
        cv::Mat readFrame();

    private:

        // ── Fixed output dimensions ───────────────────────────────────────────
        uint32_t   m_width;
        uint32_t   m_height;
        VkExtent2D m_extent{};     // = {width, height}
        VkExtent2D m_ssaaExtent{}; // = {width*4, height*4}

        // ── Core Vulkan handles ───────────────────────────────────────────────
        VkInstance       m_instance       = VK_NULL_HANDLE;
        VkPhysicalDevice m_physicalDevice = VK_NULL_HANDLE;
        VkDevice         m_device         = VK_NULL_HANDLE;
        VkQueue          m_graphicsQueue  = VK_NULL_HANDLE;
        uint32_t         m_graphicsFamily = 0;

        // ── SSAA render target (device-local, TRANSFER_SRC after render pass) ─
        VkImage        m_ssaaImage     = VK_NULL_HANDLE;
        VkDeviceMemory m_ssaaMemory    = VK_NULL_HANDLE;
        VkImageView    m_ssaaImageView = VK_NULL_HANDLE;

        // ── Readback image (linear, host-visible) ─────────────────────────────
        VkImage        m_readbackImage  = VK_NULL_HANDLE;
        VkDeviceMemory m_readbackMemory = VK_NULL_HANDLE;

        // ── Render pass / pipeline ────────────────────────────────────────────
        VkRenderPass     m_renderPass     = VK_NULL_HANDLE;
        VkFramebuffer    m_framebuffer    = VK_NULL_HANDLE;
        VkPipelineLayout m_pipelineLayout = VK_NULL_HANDLE;
        VkPipeline       m_pipeline       = VK_NULL_HANDLE;

        // ── set=0 UBO ─────────────────────────────────────────────────────────
        VkDescriptorSetLayout m_uboLayout    = VK_NULL_HANDLE;
        VkDescriptorPool      m_uboPool      = VK_NULL_HANDLE;
        VkDescriptorSet       m_uboSet       = VK_NULL_HANDLE;
        VkBuffer              m_uniformBuffer = VK_NULL_HANDLE;
        VkDeviceMemory        m_uniformMemory = VK_NULL_HANDLE;

        // ── set=1 per-mesh texture ────────────────────────────────────────────
        VkDescriptorSetLayout m_texLayout      = VK_NULL_HANDLE;
        VkDescriptorPool      m_texPool        = VK_NULL_HANDLE;
        VkDescriptorSet       m_defaultTexSet  = VK_NULL_HANDLE;

        // ── Geometry buffers ──────────────────────────────────────────────────
        VkBuffer       m_vertexBuffer = VK_NULL_HANDLE;
        VkDeviceMemory m_vertexMemory = VK_NULL_HANDLE;
        VkBuffer       m_indexBuffer  = VK_NULL_HANDLE;
        VkDeviceMemory m_indexMemory  = VK_NULL_HANDLE;

        // ── Commands ──────────────────────────────────────────────────────────
        VkCommandPool   m_commandPool   = VK_NULL_HANDLE;
        VkCommandBuffer m_commandBuffer = VK_NULL_HANDLE;

        // ── Texture resources ─────────────────────────────────────────────────
        struct TextureResource {
            VkImage        image   = VK_NULL_HANDLE;
            VkDeviceMemory memory  = VK_NULL_HANDLE;
            VkImageView    view    = VK_NULL_HANDLE;
            VkSampler      sampler = VK_NULL_HANDLE;
        };
        std::vector<TextureResource> m_textures;
        TextureResource              m_defaultTexture;

        // ── CPU-side geometry ─────────────────────────────────────────────────
        struct MeshDrawInfo { uint32_t firstIndex; uint32_t indexCount; };
        std::vector<Mesh>         m_meshes;
        std::vector<MeshDrawInfo> m_meshDrawInfos;
        std::vector<Vertex>       m_vertices;
        std::vector<uint16_t>     m_indices;
        bool                      m_geomDirty = false;

        // ── Init helpers ──────────────────────────────────────────────────────
        bool createInstance();
        bool pickPhysicalDevice();
        bool createDevice();
        bool createSsaaResources();
        bool createReadbackResources();
        bool createRenderPass();
        bool createUniformBuffer();
        bool createDescriptorSets();
        bool createPipeline();
        bool createGeometryBuffers();
        bool createCommandPool();
        bool createCommandBuffer();

        // ── Vulkan utilities ──────────────────────────────────────────────────
        uint32_t       findMemoryType(uint32_t filter, VkMemoryPropertyFlags props);
        VkShaderModule createShaderModule(const std::vector<uint32_t>& code);
        void           transitionImageLayout(VkImage image, VkImageLayout from, VkImageLayout to);
        void           copyBufferToImage(VkBuffer buf, VkImage image, uint32_t w, uint32_t h);
        void           updateUniforms();

        void cleanup();
    };

} // namespace VC
