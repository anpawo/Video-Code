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
#include <vector>

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
        float pad2[2];
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
        bool createMsaaResources();
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
        void destroyMsaaResources();

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

        // ── MSAA ─────────────────────────────────────────────────────────
        VkSampleCountFlagBits m_msaaSamples  = VK_SAMPLE_COUNT_4_BIT;
        VkImage               m_msaaImage    = VK_NULL_HANDLE;
        VkDeviceMemory        m_msaaMemory   = VK_NULL_HANDLE;
        VkImageView           m_msaaImageView = VK_NULL_HANDLE;

        // ── Swapchain ─────────────────────────────────────────────────────
        VkSwapchainKHR           m_swapchain = VK_NULL_HANDLE;
        VkFormat                 m_swapFormat{};
        VkExtent2D               m_swapExtent{};
        std::vector<VkImage>     m_swapImages;
        std::vector<VkImageView> m_swapImageViews;

        // ── Render pass & pipeline ────────────────────────────────────────
        VkRenderPass          m_renderPass = VK_NULL_HANDLE;
        VkDescriptorSetLayout m_descriptorSetLayout = VK_NULL_HANDLE;
        VkDescriptorPool      m_descriptorPool = VK_NULL_HANDLE;
        VkDescriptorSet       m_descriptorSet = VK_NULL_HANDLE;
        VkPipelineLayout      m_pipelineLayout = VK_NULL_HANDLE;
        VkPipeline            m_pipeline = VK_NULL_HANDLE;

        // ── Framebuffers & commands ───────────────────────────────────────
        std::vector<VkFramebuffer> m_framebuffers;
        VkCommandPool              m_commandPool = VK_NULL_HANDLE;
        VkCommandBuffer            m_commandBuffer = VK_NULL_HANDLE;

        // ── Synchronisation primitives ────────────────────────────────────
        VkSemaphore m_imageAvailableSemaphore = VK_NULL_HANDLE;
        VkSemaphore m_renderFinishedSemaphore = VK_NULL_HANDLE;
        VkFence     m_inFlightFence = VK_NULL_HANDLE;

        // ── Buffers & device memory ───────────────────────────────────────
        VkBuffer       m_vertexBuffer  = VK_NULL_HANDLE;
        VkDeviceMemory m_vertexMemory  = VK_NULL_HANDLE;
        VkBuffer       m_indexBuffer   = VK_NULL_HANDLE;
        VkDeviceMemory m_indexMemory   = VK_NULL_HANDLE;
        VkBuffer       m_uniformBuffer = VK_NULL_HANDLE;
        VkDeviceMemory m_uniformMemory = VK_NULL_HANDLE;

        // ── CPU-side geometry ─────────────────────────────────────────────
        struct MeshDrawInfo
        {
            uint32_t firstIndex;  // offset into the flat index buffer
            uint32_t indexCount;  // number of indices for this mesh
        };

        std::vector<Mesh>         m_meshes;
        std::vector<MeshDrawInfo> m_meshDrawInfos;
        std::vector<Vertex>       m_vertices;
        std::vector<uint16_t>     m_indices;
        bool                      m_geomDirty = false;

        // ── Frame callback ────────────────────────────────────────────────
        std::function<std::vector<Mesh>()> m_frameCallback;
    };

} // namespace VC
