/*
** EPITECH PROJECT, 2026
** video-code
** File description:
** VulkanHeadlessRenderer — pure offscreen Vulkan renderer (no window, no swapchain)
*/

#pragma once

#include <vulkan/vulkan.h>
#include <opencv2/core/mat.hpp>
#include <string>
#include <unordered_map>
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

        // Re-upload pixel data into an existing texture in-place (same dimensions assumed).
        void updateTexturePixels(VkDescriptorSet desc, const cv::Mat& mat);

        // Replace the scene geometry for the next readFrame() call.
        void setMeshes(const std::vector<Mesh>& meshes);

        // Render the current scene and submit it without waiting for the GPU.
        // Returns the PREVIOUS call's pixels (BGRA cv::Mat), which the GPU
        // finished while this call's command buffer was being recorded —
        // empty on the very first call. Call flush() after the last frame to
        // retrieve its pixels.
        cv::Mat readFrame();

        // Wait for the most recently submitted readFrame() and return its
        // pixels. Empty if readFrame() was never called.
        cv::Mat flush();

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

        // ── Readback images (linear, host-visible, double-buffered) ───────────
        // While the GPU writes frame N into m_readbackImages[curIdx], the CPU
        // may still be memcpy'ing frame N-1 out of the other slot — see readFrame().
        VkImage        m_readbackImages[2]  = {VK_NULL_HANDLE, VK_NULL_HANDLE};
        VkDeviceMemory m_readbackMemories[2] = {VK_NULL_HANDLE, VK_NULL_HANDLE};

        // ── Pipelining state ───────────────────────────────────────────────────
        // Signaled when the command buffer submitted for m_pendingIdx finishes.
        VkFence m_renderFence = VK_NULL_HANDLE;
        bool    m_hasPending  = false; // true once at least one frame has been submitted
        size_t  m_pendingIdx  = 0;     // readback slot of the most recently submitted frame

        // ── Main render pass / pipeline ───────────────────────────────────────
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
        std::vector<TextureResource>                 m_textures;
        std::unordered_map<VkDescriptorSet, size_t>  m_textureIndex;
        TextureResource                              m_defaultTexture;

        // ── CPU-side geometry ─────────────────────────────────────────────────
        struct MeshDrawInfo { uint32_t firstIndex; uint32_t indexCount; };
        std::vector<Mesh>         m_meshes;
        std::vector<MeshDrawInfo> m_meshDrawInfos;
        std::vector<Vertex>       m_vertices;
        std::vector<uint32_t>     m_indices;
        bool                      m_geomDirty = false;

        // ── Per-frame partitioned mesh indices ────────────────────────────────
        std::vector<size_t> m_effectMeshIndices;  // meshes with active effects

        // ── Effect (fragment shader) post-process infrastructure ──────────────

        // Render pass: transparent clear, SHADER_READ_ONLY_OPTIMAL final (1 sample)
        VkRenderPass  m_effectPass    = VK_NULL_HANDLE;

        // Ping/pong scratch images at output resolution (SAMPLED + COLOR_ATTACHMENT)
        VkImage        m_pingImage   = VK_NULL_HANDLE;
        VkDeviceMemory m_pingMemory  = VK_NULL_HANDLE;
        VkImageView    m_pingView    = VK_NULL_HANDLE;
        VkImage        m_pongImage   = VK_NULL_HANDLE;
        VkDeviceMemory m_pongMemory  = VK_NULL_HANDLE;
        VkImageView    m_pongView    = VK_NULL_HANDLE;
        VkFramebuffer  m_pingFb      = VK_NULL_HANDLE;
        VkFramebuffer  m_pongFb      = VK_NULL_HANDLE;

        // Sampler + descriptor sets for ping/pong source reads
        VkSampler       m_effectSampler = VK_NULL_HANDLE;
        VkDescriptorSet m_pingSrcSet    = VK_NULL_HANDLE; // effect pipeline set=0 → ping
        VkDescriptorSet m_pongSrcSet    = VK_NULL_HANDLE; // effect pipeline set=0 → pong

        // Per-effect GLSL pipeline (keyed by lowercase shader name)
        struct EffectPipeline {
            VkPipelineLayout layout   = VK_NULL_HANDLE;
            VkPipeline       pipeline = VK_NULL_HANDLE;
        };
        std::unordered_map<std::string, EffectPipeline> m_effectPipelines;

        // Static fullscreen composite quad (Vertex format, mode=3)
        VkBuffer       m_compVtxBuf = VK_NULL_HANDLE;
        VkDeviceMemory m_compVtxMem = VK_NULL_HANDLE;
        VkBuffer       m_compIdxBuf = VK_NULL_HANDLE;
        VkDeviceMemory m_compIdxMem = VK_NULL_HANDLE;

        // Per-effect-mesh result image (final effect output, sampled by the
        // composite quad in the main pass). Grow-on-demand pool, never shrinks,
        // indexed in parallel with m_effectMeshIndices.
        struct EffectResultSlot {
            VkImage         image         = VK_NULL_HANDLE;
            VkDeviceMemory  memory        = VK_NULL_HANDLE;
            VkImageView     view          = VK_NULL_HANDLE;
            VkFramebuffer   framebuffer   = VK_NULL_HANDLE;
            VkDescriptorSet descriptorSet = VK_NULL_HANDLE;
        };
        std::vector<EffectResultSlot> m_effectResults;

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
        bool createEffectResources();

        // ── Vulkan utilities ──────────────────────────────────────────────────
        uint32_t       findMemoryType(uint32_t filter, VkMemoryPropertyFlags props);
        VkShaderModule createShaderModule(const std::vector<uint32_t>& code);
        void           transitionImageLayout(VkImage image, VkImageLayout from, VkImageLayout to);
        void           copyBufferToImage(VkBuffer buf, VkImage image, uint32_t w, uint32_t h);
        void           updateUniforms();

        // Map m_readbackImages[idx]/m_readbackMemories[idx] and copy it into a cv::Mat.
        cv::Mat        copyReadback(size_t idx);

        bool           createEffectPipeline(const std::string& name);

        // Grow m_effectResults (never shrinks) so it has at least `count` slots.
        bool ensureEffectResultCapacity(size_t count);

        // ── Effect pass recording helpers ─────────────────────────────────────
        void recordEffectGeomPass(VkCommandBuffer cb, VkFramebuffer fb, size_t meshIndex);
        void recordEffectKernelPass(VkCommandBuffer cb, VkFramebuffer fb,
                                    VkDescriptorSet srcSet,
                                    const std::string& name,
                                    float texelX, float texelY,
                                    const std::vector<float>& params);

        void cleanup();
    };

} // namespace VC
