/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Core
*/

#pragma once

#include <vulkan/vulkan.h>

#include <argparse/argparse.hpp>
#include <functional>
#include <memory>
#include <opencv2/opencv.hpp>
#include <pybind11/pybind11.h>

#include "core/Config.hpp"
#include "input/IInput.hpp"

namespace py = pybind11;

namespace VC
{
    class VulkanWidget; // forward declaration for uploadTextures

    class Core
    {
    public:

        Core(const argparse::ArgumentParser& parser, const Config& config);
        ~Core() = default;

        ///< Reload the source file, then execute the stack, then add the new frames to the Timeline.
        void reloadSourceFile();

        ///< Update the current frame by generating the meshes. Returns a reference
        ///< to the internal cache — valid until the next generateMeshes() /
        ///< reloadSourceFile() call. Returning by value used to copy every vertex
        ///< of every mesh once per frame.
        const std::vector<Mesh>& generateMeshes();

        ///< Upload textures for all Image inputs to a Vulkan renderer.
        ///< uploadFn receives each image's cv::Mat and returns the VkDescriptorSet.
        void uploadTextures(VulkanWidget* widget);
        void uploadTextures(
            std::function<VkDescriptorSet(const cv::Mat&)>          uploadFn,
            std::function<void(VkDescriptorSet, const cv::Mat&)>    reuploadFn = {});

        ///< Time control
        void pause();

        void goToFirstFrame();
        void goToLastFrame();

        void goToPrevTimestamp();
        void goToNextTimestamp();

        void forwardFrame(size_t n);
        void backwardFrame(size_t n);

        // ---

        ///< Index of the frame currently being displayed
        size_t _index{0};
        size_t _nbFrame{0}; // Starting at 1 forces the first frame to be generated even without any transformations.

        ///< Information display
        const bool _showstack;
        const bool _showtimeline;

    private:

        void executeStack(const py::dict& stack, const py::list& events);

        ///< (Re)build a single input from its stack subtree (Create + Apply entries),
        ///< replacing _inputs[idx] in place. Used by both full and incremental rebuilds.
        ///< When reuseExisting is true and _inputs[idx]'s Create entry is unchanged, the
        ///< existing AInput is kept alive (skipping its — possibly expensive — constructor,
        ///< e.g. Image/Video file I/O) and only its modification state is reset + replayed.
        void rebuildInput(size_t idx, const py::dict& inputData, bool reuseExisting);

        ///< Per-input snapshot of the stack (as JSON) from the last reload — diffed against
        ///< the freshly-executed stack so reloadSourceFile() only rebuilds inputs that changed.
        std::map<int, json> _stackSnapshot{};

        ///< Indices of inputs rebuilt during the last executeStack() that need a texture
        ///< (re)upload — consumed and cleared by uploadTextures().
        std::vector<size_t> _pendingTextureUpload{};

        ///< Config (Window / Framerate / Paths)
        const Config& _config;

        ///< The video editor is paused
        bool _paused{false};
        bool _indexChanged{true};

        ///< Mesh cache — rebuilt only when the render index changes
        size_t            _lastRenderedIndex{SIZE_MAX};
        std::vector<Mesh> _cachedMeshes{};

    public:

        ///< True only when generateMeshes() actually rebuilt the meshes this call
        bool _meshesRebuilt{true};

        ///< Waits:
        std::map<size_t, size_t> _waits{};

        ///< Timestamps:
        std::map<size_t, std::string> _timestamps{};

        ///< Inputs created
        std::vector<std::unique_ptr<IInput>> _inputs{};

    };
};
