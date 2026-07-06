/*
** EPITECH PROJECT, 2026
** video-code
** File description:
** VulkanWidget
*/

#pragma once

#include <vulkan/vulkan.h>

#include <QWidget>
#include <functional>
#include <opencv2/core/mat.hpp>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

#include "vulkan/BlendModes.hpp"
#include "vulkan/Mesh.hpp"

namespace VC
{
    // -----------------------------------------------------------------------
    // UniformData
    //   The UBO uploaded to the GPU every frame, read by the fragment shader.
    //   Follows std140 alignment: pad[] arrays keep members on 16-byte boundaries.
    //
    //   GLSL layout:
    //     layout(binding = 0) uniform UBO {
    //         float time;   float pad0; float pad1; float pad2;   // 16 bytes
    //         float resX;   float resY; float pad3; float pad4;   // 16 bytes
    //     } ubo;
    // -----------------------------------------------------------------------
    struct UniformData
    {
        float time;
        float pad[3];
        float resolution[2];
        float pixelSize; // 1.0 / min(screenWidth, screenHeight) — for AA scaling
        float pad2[1];
    };

    // -----------------------------------------------------------------------
    // VulkanWidget
    //   A Qt widget that owns and drives the entire Vulkan rendering pipeline.
    //
    //   Qt integration
    //   ──────────────
    //   WA_NativeWindow      — forces a real OS window handle so CAMetalLayer works.
    //   WA_PaintOnScreen     — bypasses Qt's compositor; Vulkan writes directly.
    //   WA_NoSystemBackground — prevents Qt's background fill overwriting Vulkan output.
    //   paintEngine() → nullptr — signals Qt not to use QPainter into this widget.
    //   Every Qt repaint calls paintEvent() which forwards to render().
    //
    //   Lifecycle
    //   ─────────
    //   init() must be called once after the widget is shown so the native WId exists.
    //   cleanup() is called from the destructor in reverse-creation order.
    // -----------------------------------------------------------------------
    class VulkanWidget : public QWidget
    {
        Q_OBJECT

    public:

        explicit VulkanWidget(QWidget* parent = nullptr);
        ~VulkanWidget() override;

        // init() — run all Vulkan initialisation steps in order.
        // Must be called after show(); returns false and logs on first failure.
        bool init();

        // setMeshes() — replace the scene geometry for the next frame.
        // Flattens all mesh vertices and indices into the shared buffers and
        // marks them dirty so recordCommandBuffer() re-uploads before drawing.
        void setMeshes(const std::vector<Mesh>& meshes);

        // setFrameCallback() — called every frame before rendering to advance
        // the animation. Replaces the separate QTimer-driven loop so that
        // animation advances are display-synchronized via requestUpdate().
        void setFrameCallback(std::function<std::vector<Mesh>()> cb);

        // uploadTexture() — upload a cv::Mat (BGRA) to the GPU as a texture.
        // Returns a VkDescriptorSet (set=1 layout) to store in the Mesh.
        // Must be called after init(). The widget owns all GPU resources;
        // they are freed in cleanup().
        VkDescriptorSet uploadTexture(const cv::Mat& mat);

        // updateTexturePixels() — re-upload pixel data into an existing texture in-place.
        // Descriptor set, image, view and sampler are reused; only pixel data changes.
        // Same dimensions as the original upload are assumed.
        void updateTexturePixels(VkDescriptorSet desc, const cv::Mat& mat);

        // readFrame() — render the current scene offscreen and return the pixels
        // as a BGRA cv::Mat at the widget's current size (m_swapExtent). Used by
        // the preview window's frame-export hotkey (Ctrl+S).
        // Must be called after init() and setMeshes(). Blocks until GPU is done.
        cv::Mat readFrame();

    protected:

        bool event(QEvent* e) override;
        bool eventFilter(QObject* obj, QEvent* e) override;
        void paintEvent(QPaintEvent*) override;
        void resizeEvent(QResizeEvent*) override;

        // Returning nullptr tells Qt this widget handles all its own painting.
        QPaintEngine* paintEngine() const override { return nullptr; }

    private:

        // ── Initialisation helpers (called once from init()) ──────────────
        bool createInstance();
        bool createSurface();
        bool pickPhysicalDevice();
        bool createDevice();
        bool createSwapchain();
        bool createSsaaResources();
        void destroySsaaResources();
        bool createReadbackResources();
        void destroyReadbackResources();
        bool createRenderPass();
        bool createUniformBuffer();
        bool createDescriptorSet();
        bool createPipeline();
        bool createVertexBuffer();
        bool createIndexBuffer();
        bool createFramebuffers();
        bool createCommandPool();
        bool createCommandBuffers();
        bool createSyncObjects();

        // ── Per-frame helpers ─────────────────────────────────────────────
        void updateUniforms();
        void recordCommandBuffer(VkCommandBuffer cb, uint32_t imageIndex);

        // ── Lifecycle helpers ─────────────────────────────────────────────
        void recreateSwapchain();
        void cleanup();
        void render();

        // ── Vulkan utilities ──────────────────────────────────────────────
        VkShaderModule createShaderModule(const std::vector<uint32_t>& code);
        uint32_t       findMemoryType(uint32_t filter, VkMemoryPropertyFlags props);

        // Texture upload helpers
        void transitionImageLayout(VkImage image, VkImageLayout from, VkImageLayout to);
        void copyBufferToImage(VkBuffer buf, VkImage image, uint32_t w, uint32_t h);

        // ── Platform ──────────────────────────────────────────────────────
        void* m_metalLayer = nullptr; // Opaque CAMetalLayer* (macOS drawable surface).
        bool  m_initialized = false;  // Guards render() against calls before init().

        // ── Core Vulkan handles ───────────────────────────────────────────
        VkInstance       m_instance = VK_NULL_HANDLE;
        VkSurfaceKHR     m_surface = VK_NULL_HANDLE;
        VkPhysicalDevice m_physicalDevice = VK_NULL_HANDLE;
        VkDevice         m_device = VK_NULL_HANDLE;
        VkQueue          m_graphicsQueue = VK_NULL_HANDLE;
        uint32_t         m_graphicsFamily = 0;

        // ── Swapchain ─────────────────────────────────────────────────────
        VkSwapchainKHR           m_swapchain = VK_NULL_HANDLE;
        VkFormat                 m_swapFormat{};
        VkExtent2D               m_swapExtent{};
        std::vector<VkImage>     m_swapImages;
        std::vector<VkImageView> m_swapImageViews;

        // ── MSAA color attachment (4×, swapchain resolution) ─────────────
        VkExtent2D     m_ssaaExtent{};
        VkImage        m_ssaaImage = VK_NULL_HANDLE;
        VkDeviceMemory m_ssaaMemory = VK_NULL_HANDLE;
        VkImageView    m_ssaaImageView = VK_NULL_HANDLE;

        // ── Resolve image (1 sample, used by readFrame framebuffer) ───────
        VkImage        m_resolveImage = VK_NULL_HANDLE;
        VkDeviceMemory m_resolveMemory = VK_NULL_HANDLE;
        VkImageView    m_resolveImageView = VK_NULL_HANDLE;

        // ── Readback image (linear, host-visible, swapchain resolution) ───
        VkImage        m_readbackImage = VK_NULL_HANDLE;
        VkDeviceMemory m_readbackMemory = VK_NULL_HANDLE;

        // ── Render pass & pipeline ────────────────────────────────────────
        VkRenderPass m_renderPass = VK_NULL_HANDLE;

        // set = 0: UBO
        VkDescriptorSetLayout m_descriptorSetLayout = VK_NULL_HANDLE;
        VkDescriptorPool      m_descriptorPool = VK_NULL_HANDLE;
        VkDescriptorSet       m_descriptorSet = VK_NULL_HANDLE;

        // set = 1: per-mesh texture (combined image sampler)
        VkDescriptorSetLayout m_textureSetLayout = VK_NULL_HANDLE;
        VkDescriptorPool      m_texturePool = VK_NULL_HANDLE;
        VkDescriptorSet       m_defaultTextureSet = VK_NULL_HANDLE; // 1×1 white, bound for non-textured meshes

        VkPipelineLayout m_pipelineLayout = VK_NULL_HANDLE;
        // One pipeline per blend mode (index = Mesh::blendMode). All share
        // m_pipelineLayout and every other state — only pColorBlendState differs.
        // m_pipelines[0] is Normal, the default main-scene pipeline.
        VkPipeline       m_pipelines[kBlendModeCount] = {};

        // ── Texture resources ─────────────────────────────────────────────
        struct TextureResource
        {
            VkImage        image = VK_NULL_HANDLE;
            VkDeviceMemory memory = VK_NULL_HANDLE;
            VkImageView    view = VK_NULL_HANDLE;
            VkSampler      sampler = VK_NULL_HANDLE;
        };

        std::vector<TextureResource>                m_textures;       // one per uploadTexture() call
        std::unordered_map<VkDescriptorSet, size_t> m_textureIndex;   // descriptor → m_textures index
        TextureResource                             m_defaultTexture; // the 1×1 white default

        // ── Framebuffers & commands ───────────────────────────────────────
        std::vector<VkFramebuffer> m_framebuffers;
        VkCommandPool              m_commandPool = VK_NULL_HANDLE;
        VkCommandBuffer            m_commandBuffer = VK_NULL_HANDLE;

        // ── Synchronisation primitives ────────────────────────────────────
        VkSemaphore m_imageAvailableSemaphore = VK_NULL_HANDLE;
        VkSemaphore m_renderFinishedSemaphore = VK_NULL_HANDLE;
        VkFence     m_inFlightFence = VK_NULL_HANDLE;

        // ── Buffers & device memory ───────────────────────────────────────
        VkBuffer       m_vertexBuffer = VK_NULL_HANDLE;
        VkDeviceMemory m_vertexMemory = VK_NULL_HANDLE;
        VkBuffer       m_indexBuffer = VK_NULL_HANDLE;
        VkDeviceMemory m_indexMemory = VK_NULL_HANDLE;
        VkBuffer       m_uniformBuffer = VK_NULL_HANDLE;
        VkDeviceMemory m_uniformMemory = VK_NULL_HANDLE;

        // ── CPU-side geometry ─────────────────────────────────────────────
        struct MeshDrawInfo
        {
            uint32_t firstIndex; // offset into the flat index buffer
            uint32_t indexCount; // number of indices for this mesh
        };

        std::vector<Mesh>         m_meshes;
        std::vector<MeshDrawInfo> m_meshDrawInfos;
        std::vector<Vertex>       m_vertices;
        std::vector<uint32_t>     m_indices;
        bool                      m_geomDirty = false;

        // ── Per-frame partitioned mesh indices ────────────────────────────
        // Meshes needing an isolated pre-pass: those with a GLSL effect chain,
        // matte consumers, and matte sources. See headless renderer for the
        // matte design (both renderers stay mirrored).
        std::vector<size_t> m_effectMeshIndices;

        // Matte plumbing: inputIndex→mesh position (identity lookup for a
        // consumer's source, since mesh order ≠ input order), and the set of
        // source mesh positions excluded from the main draw loop.
        std::unordered_map<int, size_t> m_inputIndexToMeshPos;
        std::unordered_set<size_t>      m_matteSourceMeshPositions;

        // Adjustment-layer mesh positions, ascending (see the headless renderer
        // for the full rationale — both stay mirrored). Empty = no adjustment
        // layers → the flatten path never runs and the scene draws unchanged.
        std::vector<size_t> m_adjustmentMeshPositions;

        // ── Effect post-process infrastructure ────────────────────────────
        VkRenderPass    m_effectPass = VK_NULL_HANDLE;     // 1× kernel pass
        VkRenderPass    m_effectGeomPass = VK_NULL_HANDLE; // 4× MSAA → resolve to ping
        VkImage         m_pingImage = VK_NULL_HANDLE;
        VkDeviceMemory  m_pingMemory = VK_NULL_HANDLE;
        VkImageView     m_pingView = VK_NULL_HANDLE;
        VkImage         m_pongImage = VK_NULL_HANDLE;
        VkDeviceMemory  m_pongMemory = VK_NULL_HANDLE;
        VkImageView     m_pongView = VK_NULL_HANDLE;
        VkFramebuffer   m_pingFb = VK_NULL_HANDLE;
        VkFramebuffer   m_pongFb = VK_NULL_HANDLE;
        VkFramebuffer   m_effectGeomFb = VK_NULL_HANDLE; // [msaaView, pingView]
        VkImage         m_effectMsaaImage = VK_NULL_HANDLE;
        VkDeviceMemory  m_effectMsaaMemory = VK_NULL_HANDLE;
        VkImageView     m_effectMsaaView = VK_NULL_HANDLE;
        VkSampler       m_effectSampler = VK_NULL_HANDLE;
        VkDescriptorSet m_pingSrcSet = VK_NULL_HANDLE;
        VkDescriptorSet m_pongSrcSet = VK_NULL_HANDLE;

        // ── Glow/bloom: hand-built exception to the effect-chain rules ─────────
        // Preserves the sharp original past blur's in-place H/V passes (in a
        // third scratch buffer) and additively composites the blurred copy back
        // on top via a LOAD render pass + additive-blend pipeline. See the
        // `lower == "glow"` branch in recordEffectPrepasses().
        VkRenderPass    m_effectPassLoad = VK_NULL_HANDLE; // == m_effectPass but loadOp = LOAD
        VkImage         m_thirdImage = VK_NULL_HANDLE;
        VkDeviceMemory  m_thirdMemory = VK_NULL_HANDLE;
        VkImageView     m_thirdView = VK_NULL_HANDLE;
        VkFramebuffer   m_thirdFb = VK_NULL_HANDLE;
        VkDescriptorSet m_thirdSrcSet = VK_NULL_HANDLE;

        // 4× MSAA geometry pipeline for effect ping pass
        VkPipeline m_effectGeomPipeline = VK_NULL_HANDLE;

        // Blend-mode pipelines parallel to m_pipelines[] but built for the
        // 1-sample m_effectPass (not the 4× MSAA main render pass) — REQUIRED
        // ONLY here, not in the headless renderer. The adjustment-layer flatten
        // pass composites MANY meshes with their individual blend modes into a
        // 1-sample scratch (ping); m_pipelines[] are 4× MSAA and cannot bind in
        // m_effectPass, and m_effectGeomPipeline is single-mesh Normal-only. So
        // the flatten needs its own 1-sample blend-mode array. See the
        // renderer-asymmetry note in docs/ADDING_EFFECTS.md.
        VkPipeline m_effectBlendPipelines[kBlendModeCount] = {};

        struct EffectPipeline
        {
            VkPipelineLayout layout = VK_NULL_HANDLE;
            VkPipeline       pipeline = VK_NULL_HANDLE;
        };

        std::unordered_map<std::string, EffectPipeline> m_effectPipelines;

        // Additive-blend pipeline for glow's combine pass (blendEnable + LOAD
        // render pass), built by createGlowResources() outside the generic
        // auto-discovery loop.
        EffectPipeline m_glowCombine;

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

        // ── Track matte: 2-sampler combine (content + matte) — mirrors the
        // headless renderer. Second hand-built exception to "one texture, no
        // compositing" (after glow); first feature where two inputs interact. ──
        VkDescriptorSetLayout        m_matteLayout = VK_NULL_HANDLE;
        VkDescriptorPool             m_mattePool = VK_NULL_HANDLE;
        EffectPipeline               m_matteCombine;
        std::vector<VkDescriptorSet> m_matteSets; // one per matte combine, grown on demand

        // ── LUT color grade: the THIRD hand-built exception (after glow, matte)
        // — mirrors the headless renderer. Unlike every other effect it needs a
        // texture uploaded ONCE from a .cube file and reused every frame, keyed
        // by file path in m_lutCache (a .cube's blue slices tiled into one 2D
        // atlas, see LutAtlas.hpp). 2-sampler combine (content + atlas) with
        // push constants (intensity + size); `lut` folder skipped by the generic
        // auto-discovery loop. Built by createLutResources(). ───────────────────
        VkDescriptorSetLayout        m_lutLayout = VK_NULL_HANDLE;
        VkDescriptorPool             m_lutPool = VK_NULL_HANDLE;
        EffectPipeline               m_lutCombine;
        std::vector<VkDescriptorSet> m_lutSets; // one per lut combine, grown on demand

        // A parsed+uploaded LUT atlas. image/memory owned by m_textures (built
        // via uploadTexture, freed in cleanup); this bundles the view/sampler to
        // bind + the LUT edge size N the shader needs.
        struct LutResource
        {
            VkImageView view = VK_NULL_HANDLE;
            VkSampler   sampler = VK_NULL_HANDLE;
            int         size = 0; // N
        };
        std::unordered_map<std::string, LutResource> m_lutCache; // filepath → atlas

        bool createEffectResources();
        bool createEffectPipeline(const std::string& name);

        // Build glow-only extras: m_effectPassLoad, third scratch buffer, m_glowCombine.
        bool createGlowResources();

        // Build the matte-only extras: 2-sampler layout/pool + combine pipeline.
        bool createMatteResources();

        // Build the LUT-only extras: 2-sampler layout/pool + combine pipeline
        // (with push constants).
        bool createLutResources();

        // Parse+upload the .cube at `filepath` into a cached atlas (once per
        // unique path), returning it — or nullptr if the file can't be loaded.
        const LutResource* getOrBuildLut(const std::string& filepath);

        // Grow m_effectResults (never shrinks) so it has at least `count` slots.
        bool ensureEffectResultCapacity(size_t count);

        // Grow m_matteSets (never shrinks) so it has at least `count` sets.
        bool ensureMatteSetCapacity(size_t count);

        // Grow m_lutSets (never shrinks) so it has at least `count` sets.
        bool ensureLutSetCapacity(size_t count);

        void recordEffectGeomPass(VkCommandBuffer cb, size_t meshIndex);
        void recordEffectKernelPass(VkCommandBuffer cb, VkFramebuffer fb, VkDescriptorSet srcSet, const std::string& name, float texelX, float texelY, const std::vector<float>& params);
        // Glow additive combine: LOAD the original already in `fb`, add
        // intensity*blurred (sampled through `srcSet`) on top (m_glowCombine).
        void recordGlowCombinePass(VkCommandBuffer cb, VkFramebuffer fb, VkDescriptorSet srcSet, float intensity);
        // Matte combine: sample `set` (binding 0 = content, binding 1 = matte)
        // and write the masked result into `fb` (m_matteCombine).
        void recordMatteCombinePass(VkCommandBuffer cb, VkFramebuffer fb, VkDescriptorSet set);
        // LUT combine: sample `set` (binding 0 = content, binding 1 = LUT atlas)
        // and write the graded result into `fb` (m_lutCombine). `intensity`
        // dissolves original↔graded; `lutSize` is the atlas edge N.
        void recordLutCombinePass(VkCommandBuffer cb, VkFramebuffer fb, VkDescriptorSet set, float intensity, float lutSize);

        // Per-mesh effect pre-passes: geometry + effect chain → m_effectResults,
        // followed by the matte-combine phase (masks consumers in place).
        void recordEffectPrepasses(VkCommandBuffer cb);

        // Single zIndex-ordered draw loop: normal mesh geometry interleaved
        // with effect-mesh composite quads. Assumes the render pass, viewport/
        // scissor, pipeline and set=0 descriptor are already bound.
        void recordSceneDraws(VkCommandBuffer cb);

        // ── Adjustment-layer support (mirrors the headless renderer) ──────────
        // Draw meshes [begin,end) into the active render pass; `pipelines` is the
        // blend-pipeline array to bind from — m_pipelines[] for the main pass,
        // m_effectBlendPipelines[] (1-sample) for the flatten pass.
        void recordMeshRange(VkCommandBuffer cb, size_t begin, size_t end,
                             const std::unordered_map<size_t, size_t>& effectSlotForMesh,
                             const VkPipeline* pipelines);
        // Composite one effect-result image as a fullscreen quad (set=0 assumed
        // bound), binding `pipeline` (main-pass MSAA or flatten-pass 1-sample).
        void recordCompositeResultQuad(VkCommandBuffer cb, VkPipeline pipeline, VkDescriptorSet resultSet);
        // Flatten meshes [begin,end) into m_pingFb (1-sample, transparent clear),
        // optionally seeded with a previous adjustment layer's graded result.
        void recordAdjustmentFlattenPass(VkCommandBuffer cb, size_t begin, size_t end, int seedSlot,
                                         const std::unordered_map<size_t, size_t>& effectSlotForMesh);

        // ── Frame callback ────────────────────────────────────────────────
        std::function<std::vector<Mesh>()> m_frameCallback;
    };

} // namespace VC
