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
#include <array>
#include <unordered_map>
#include <unordered_set>
#include <vector>

#include "vulkan/BlendModes.hpp"
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

        // Opt-in transparent background for the main SSAA pass. When true the
        // pass clears to {0,0,0,0} so empty scene regions keep alpha=0 and reach
        // the readback verbatim (used for alpha-preserving exports: ProRes 4444,
        // WebM/VP9-alpha). Default false keeps the historical opaque gray clear
        // ({0.2,0.2,0.2,1.0}) — byte-identical to every existing golden/PNG/MP4.
        void setTransparentBackground(bool transparent) { m_transparentClear = transparent; }

        // Clear color of the main pass (the script's `BG` global, via
        // Core::_bgColor). Ignored while m_transparentClear is set.
        void setBackgroundColor(const std::array<float, 3>& c) { m_bgColor = c; }

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
        VkInstance       m_instance = VK_NULL_HANDLE;
        VkPhysicalDevice m_physicalDevice = VK_NULL_HANDLE;
        VkDevice         m_device = VK_NULL_HANDLE;
        VkQueue          m_graphicsQueue = VK_NULL_HANDLE;
        uint32_t         m_graphicsFamily = 0;

        // ── SSAA render target (device-local, TRANSFER_SRC after render pass) ─
        VkImage        m_ssaaImage = VK_NULL_HANDLE;
        VkDeviceMemory m_ssaaMemory = VK_NULL_HANDLE;
        VkImageView    m_ssaaImageView = VK_NULL_HANDLE;

        // ── Readback images (linear, host-visible, double-buffered) ───────────
        // While the GPU writes frame N into m_readbackImages[curIdx], the CPU
        // may still be memcpy'ing frame N-1 out of the other slot — see readFrame().
        VkImage        m_readbackImages[2] = {VK_NULL_HANDLE, VK_NULL_HANDLE};
        VkDeviceMemory m_readbackMemories[2] = {VK_NULL_HANDLE, VK_NULL_HANDLE};

        // ── Pipelining state ───────────────────────────────────────────────────
        // Signaled when the command buffer submitted for m_pendingIdx finishes.
        VkFence m_renderFence = VK_NULL_HANDLE;
        bool    m_hasPending = false; // true once at least one frame has been submitted
        size_t  m_pendingIdx = 0;     // readback slot of the most recently submitted frame

        // ── Main render pass / pipeline ───────────────────────────────────────
        VkRenderPass     m_renderPass = VK_NULL_HANDLE;
        VkFramebuffer    m_framebuffer = VK_NULL_HANDLE;
        VkPipelineLayout m_pipelineLayout = VK_NULL_HANDLE;
        // One pipeline per blend mode (index = Mesh::blendMode). All share
        // m_pipelineLayout and every other state — only pColorBlendState differs.
        // m_pipelines[0] (Normal) is also reused for the effect isolated-layer pass.
        VkPipeline       m_pipelines[kBlendModeCount] = {};

        // ── set=0 UBO ─────────────────────────────────────────────────────────
        VkDescriptorSetLayout m_uboLayout = VK_NULL_HANDLE;
        VkDescriptorPool      m_uboPool = VK_NULL_HANDLE;
        VkDescriptorSet       m_uboSet = VK_NULL_HANDLE;
        VkBuffer              m_uniformBuffer = VK_NULL_HANDLE;
        VkDeviceMemory        m_uniformMemory = VK_NULL_HANDLE;

        // ── set=1 per-mesh texture ────────────────────────────────────────────
        VkDescriptorSetLayout m_texLayout = VK_NULL_HANDLE;
        VkDescriptorPool      m_texPool = VK_NULL_HANDLE;
        VkDescriptorSet       m_defaultTexSet = VK_NULL_HANDLE;

        // ── Geometry buffers ──────────────────────────────────────────────────
        VkBuffer       m_vertexBuffer = VK_NULL_HANDLE;
        VkDeviceMemory m_vertexMemory = VK_NULL_HANDLE;
        VkBuffer       m_indexBuffer = VK_NULL_HANDLE;
        VkDeviceMemory m_indexMemory = VK_NULL_HANDLE;

        // ── Commands ──────────────────────────────────────────────────────────
        VkCommandPool   m_commandPool = VK_NULL_HANDLE;
        VkCommandBuffer m_commandBuffer = VK_NULL_HANDLE;

        // ── Texture resources ─────────────────────────────────────────────────
        struct TextureResource
        {
            VkImage        image = VK_NULL_HANDLE;
            VkDeviceMemory memory = VK_NULL_HANDLE;
            VkImageView    view = VK_NULL_HANDLE;
            VkSampler      sampler = VK_NULL_HANDLE;
        };

        std::vector<TextureResource>                m_textures;
        std::unordered_map<VkDescriptorSet, size_t> m_textureIndex;
        TextureResource                             m_defaultTexture;

        // ── CPU-side geometry ─────────────────────────────────────────────────
        struct MeshDrawInfo
        {
            uint32_t firstIndex;
            uint32_t indexCount;
        };

        std::vector<Mesh>         m_meshes;
        std::vector<MeshDrawInfo> m_meshDrawInfos;
        std::vector<Vertex>       m_vertices;
        std::vector<uint32_t>     m_indices;
        bool                      m_geomDirty = false;

        // When true the main SSAA pass clears to transparent instead of the
        // opaque gray default — see setTransparentBackground(). Off by default so
        // all existing render paths (PNG/MP4 export, visual-test goldens) are
        // untouched; only the alpha-preserving video exports flip it on.
        bool                      m_transparentClear = false;
        std::array<float, 3> m_bgColor{0.2f, 0.2f, 0.2f};

        // ── Per-frame partitioned mesh indices ────────────────────────────────
        // Meshes that need an isolated pre-pass: those with a GLSL effect chain,
        // matte consumers, AND matte sources (so their finished layer exists for
        // the combine). The main draw loop composites their EffectResultSlot.
        std::vector<size_t> m_effectMeshIndices;

        // Matte plumbing (see the matte phase in readFrame()). inputIndex→mesh
        // position lets a matte consumer find its source mesh by identity
        // (mesh order ≠ input order after filtering + zIndex sort). The set of
        // source mesh positions is excluded from the main draw loop — a matte
        // source is consumed only as a mask, never composited directly.
        std::unordered_map<int, size_t> m_inputIndexToMeshPos;
        std::unordered_set<size_t>      m_matteSourceMeshPositions;

        // Adjustment-layer mesh positions, ascending (m_meshes is z-sorted, so a
        // linear scan yields them in order). Each is a chunk boundary: the range
        // below it is flattened + graded through this layer's effect chain, and
        // the topmost one's graded result seeds the main pass. Empty = no
        // adjustment layers, and the whole feature is a no-op (main pass unchanged).
        std::vector<size_t> m_adjustmentMeshPositions;

        // ── Effect (fragment shader) post-process infrastructure ──────────────

        // Render pass: transparent clear, SHADER_READ_ONLY_OPTIMAL final (1 sample)
        VkRenderPass m_effectPass = VK_NULL_HANDLE;

        // Ping/pong scratch images at output resolution (SAMPLED + COLOR_ATTACHMENT)
        VkImage        m_pingImage = VK_NULL_HANDLE;
        VkDeviceMemory m_pingMemory = VK_NULL_HANDLE;
        VkImageView    m_pingView = VK_NULL_HANDLE;
        VkImage        m_pongImage = VK_NULL_HANDLE;
        VkDeviceMemory m_pongMemory = VK_NULL_HANDLE;
        VkImageView    m_pongView = VK_NULL_HANDLE;
        VkFramebuffer  m_pingFb = VK_NULL_HANDLE;
        VkFramebuffer  m_pongFb = VK_NULL_HANDLE;

        // Sampler + descriptor sets for ping/pong source reads
        VkSampler       m_effectSampler = VK_NULL_HANDLE;
        VkDescriptorSet m_pingSrcSet = VK_NULL_HANDLE; // effect pipeline set=0 → ping
        VkDescriptorSet m_pongSrcSet = VK_NULL_HANDLE; // effect pipeline set=0 → pong

        // ── Glow/bloom: the one hand-built exception to the effect-chain rules ──
        // Glow must (a) preserve the sharp original past blur's in-place H/V
        // passes and (b) additively composite the blurred copy back onto it.
        // That needs a THIRD scratch buffer (the ping/pong pair is consumed by
        // the blur) plus a LOAD render pass + additive-blend pipeline — neither
        // expressible through the generic single-sampler, CLEAR/blend-disabled
        // effect pipelines. See the `lower == "glow"` branch in readFrame().
        VkRenderPass    m_effectPassLoad = VK_NULL_HANDLE; // == m_effectPass but loadOp = LOAD
        VkImage         m_thirdImage = VK_NULL_HANDLE;
        VkDeviceMemory  m_thirdMemory = VK_NULL_HANDLE;
        VkImageView     m_thirdView = VK_NULL_HANDLE;
        VkFramebuffer   m_thirdFb = VK_NULL_HANDLE;
        VkDescriptorSet m_thirdSrcSet = VK_NULL_HANDLE; // effect pipeline set=0 → third

        // Per-effect GLSL pipeline (keyed by lowercase shader name)
        struct EffectPipeline
        {
            VkPipelineLayout layout = VK_NULL_HANDLE;
            VkPipeline       pipeline = VK_NULL_HANDLE;
        };

        std::unordered_map<std::string, EffectPipeline> m_effectPipelines;

        // Runtime-loaded MathShader files that failed to open/compile —
        // remembered so a broken file is logged once, not retried every frame.
        std::unordered_set<std::string> m_mathFailed;

        // Additive-blend pipeline for glow's combine pass: samples the blurred
        // copy, multiplies by intensity in glow/frag.glsl, and the (ONE, ONE)
        // blend state adds it onto the original already sitting in the target.
        // Hand-built (not from the auto-discovery loop, which forces
        // blendEnable=false + a CLEAR pass) and bound only via recordGlowCombinePass.
        EffectPipeline m_glowCombine;

        // Static fullscreen composite quad (Vertex format, mode=3)
        VkBuffer       m_compVtxBuf = VK_NULL_HANDLE;
        VkDeviceMemory m_compVtxMem = VK_NULL_HANDLE;
        VkBuffer       m_compIdxBuf = VK_NULL_HANDLE;
        VkDeviceMemory m_compIdxMem = VK_NULL_HANDLE;

        // Per-effect-mesh result image (final effect output, sampled by the
        // composite quad in the main pass). Grow-on-demand pool, never shrinks,
        // indexed in parallel with m_effectMeshIndices.
        struct EffectResultSlot
        {
            VkImage         image = VK_NULL_HANDLE;
            VkDeviceMemory  memory = VK_NULL_HANDLE;
            VkImageView     view = VK_NULL_HANDLE;
            VkFramebuffer   framebuffer = VK_NULL_HANDLE;
            VkDescriptorSet descriptorSet = VK_NULL_HANDLE;
        };

        std::vector<EffectResultSlot> m_effectResults;

        // ── Track matte: the SECOND hand-built exception to "one texture, no
        // compositing" (after glow), and the first feature where two DIFFERENT
        // inputs interact at draw time. The combine pass samples the consumer's
        // own isolated layer + the source's finished layer through a 2-sampler
        // descriptor set (binding 0 = content, binding 1 = matte) — the first
        // 2-sampler layout in the codebase. matte/frag.glsl keeps the consumer
        // only where the matte has coverage. Built by createMatteResources();
        // the `matte` folder is skipped by the generic auto-discovery loop. ─────
        VkDescriptorSetLayout m_matteLayout = VK_NULL_HANDLE; // 2 combined-image-samplers
        VkDescriptorPool      m_mattePool = VK_NULL_HANDLE;
        EffectPipeline        m_matteCombine;
        // One descriptor set per matte combine in the frame — a set can't be
        // re-pointed mid-command-buffer, so each combine needs its own. Grown
        // on demand (never shrinks), re-written each frame with the live views.
        std::vector<VkDescriptorSet> m_matteSets;

        // ── LUT color grade: the THIRD hand-built exception (after glow, matte).
        // Unlike every other effect, it needs a texture uploaded ONCE from a
        // .cube file and reused every frame — a persistent, file-keyed GPU
        // resource attached to the effect instance, not per-frame push-constant
        // math. The atlas (a .cube's blue slices tiled into one 2D image, see
        // LutAtlas.hpp) is built lazily the first time a filepath is seen and
        // cached here across frames/meshes. The combine pass is 2-sampler like
        // matte (binding 0 = content, binding 1 = LUT atlas) but adds push
        // constants (intensity + size); the `lut` folder is skipped by the
        // generic auto-discovery loop. Built by createLutResources(). ──────────
        VkDescriptorSetLayout m_lutLayout = VK_NULL_HANDLE; // 2 combined-image-samplers
        VkDescriptorPool      m_lutPool = VK_NULL_HANDLE;
        EffectPipeline        m_lutCombine;
        std::vector<VkDescriptorSet> m_lutSets; // one per lut combine, grown on demand

        // A parsed+uploaded LUT atlas. The image/memory are owned by m_textures
        // (built via uploadTexture, freed in cleanup); this only bundles the
        // view/sampler to bind + the LUT edge size N the shader needs.
        struct LutResource
        {
            VkImageView view = VK_NULL_HANDLE;
            VkSampler   sampler = VK_NULL_HANDLE;
            int         size = 0; // N
        };
        std::unordered_map<std::string, LutResource> m_lutCache; // filepath → atlas

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
        cv::Mat copyReadback(size_t idx);

        bool createEffectPipeline(const std::string& name);
        bool createEffectPipelineFromSource(const std::string& key, const std::string& fragSrc);
        // Compile-once cache for runtime-loaded MathShader files (see the
        // mathPipelineKey/ensureMathPipeline comments in the .cpp).
        bool ensureMathPipeline(const std::string& path);

        // Build the glow-only extras: m_effectPassLoad, the third scratch
        // buffer, and m_glowCombine. Called from createEffectResources().
        bool createGlowResources();

        // Build the matte-only extras: the 2-sampler descriptor layout/pool and
        // the combine pipeline. Called from createEffectResources().
        bool createMatteResources();

        // Build the LUT-only extras: the 2-sampler descriptor layout/pool and
        // the combine pipeline (with push constants). Called from
        // createEffectResources().
        bool createLutResources();

        // Parse+upload the .cube at `filepath` into a cached atlas (once per
        // unique path), returning it — or nullptr if the file can't be loaded.
        const LutResource* getOrBuildLut(const std::string& filepath);

        // Grow m_lutSets (never shrinks) so it has at least `count` sets.
        bool ensureLutSetCapacity(size_t count);

        // Grow m_effectResults (never shrinks) so it has at least `count` slots.
        bool ensureEffectResultCapacity(size_t count);

        // Grow m_matteSets (never shrinks) so it has at least `count` sets.
        bool ensureMatteSetCapacity(size_t count);

        // ── Effect pass recording helpers ─────────────────────────────────────
        void recordEffectGeomPass(VkCommandBuffer cb, VkFramebuffer fb, size_t meshIndex);

        // Draw meshes [begin,end) into the already-active render pass (viewport +
        // set=0 UBO must be bound by the caller). Shared by the main SSAA pass and
        // each adjustment-layer flatten pass: skips matte sources + adjustment
        // layers, binds the per-mesh blend pipeline, and draws raw geometry or the
        // mesh's own effect-result composite quad. `pipelines` is the blend-pipeline
        // array to bind from (m_pipelines works in both passes here — it is
        // format/sample-compatible with m_effectPass; see recordEffectGeomPass).
        void recordMeshRange(VkCommandBuffer cb, size_t begin, size_t end,
                             const std::unordered_map<size_t, size_t>& effectSlotForMesh,
                             const VkPipeline* pipelines);
        // Composite one effect-result image as a fullscreen quad (set=0 assumed
        // bound). Used to seed a flatten chunk / the main pass with a prior
        // adjustment layer's graded result, and internally by recordMeshRange.
        void recordCompositeResultQuad(VkCommandBuffer cb, VkPipeline pipeline, VkDescriptorSet resultSet);
        // Flatten meshes [begin,end) into m_pingFb (transparent clear), optionally
        // seeded first with a previous adjustment layer's graded result (seedSlot,
        // -1 = none). The caller then runs the adjustment layer's effect chain over
        // ping exactly as for a normal effect mesh — see readFrame().
        void recordAdjustmentFlattenPass(VkCommandBuffer cb, size_t begin, size_t end, int seedSlot,
                                         const std::unordered_map<size_t, size_t>& effectSlotForMesh);
        void recordEffectKernelPass(VkCommandBuffer cb, VkFramebuffer fb, VkDescriptorSet srcSet, const std::string& name, float texelX, float texelY, const std::vector<float>& params);
        // Glow additive combine: LOAD the original already in `fb`, add
        // intensity*blurred sampled through `srcSet` on top (m_glowCombine).
        void recordGlowCombinePass(VkCommandBuffer cb, VkFramebuffer fb, VkDescriptorSet srcSet, float intensity);
        // Matte combine: sample `set` (binding 0 = content, binding 1 = matte)
        // and write the masked result into `fb` (m_matteCombine).
        void recordMatteCombinePass(VkCommandBuffer cb, VkFramebuffer fb, VkDescriptorSet set);

        // LUT combine: sample `set` (binding 0 = content, binding 1 = LUT atlas)
        // and write the graded result into `fb` (m_lutCombine). `intensity`
        // dissolves original↔graded; `lutSize` is the atlas edge N.
        void recordLutCombinePass(VkCommandBuffer cb, VkFramebuffer fb, VkDescriptorSet set, float intensity, float lutSize);

        void cleanup();
    };

} // namespace VC
