/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Core
*/

#pragma once

#include <pybind11/pybind11.h>
#include <vulkan/vulkan.h>

#include <argparse/argparse.hpp>
#include <array>
#include <chrono>
#include <functional>
#include <memory>
#include <opencv2/opencv.hpp>

#include "core/Config.hpp"
#include "input/AInput.hpp" // ClockStops
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
            std::function<VkDescriptorSet(const cv::Mat&)>       uploadFn,
            std::function<void(VkDescriptorSet, const cv::Mat&)> reuploadFn = {}
        );

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

        ///< Frame clear color, normalized RGB — mirrors the script's `BG`
        ///< global (Context.backgroundColor, resolved by serialize.py and
        ///< read in executeStack; None → the historical dark gray).
        ///< Renderers pick it up next to setMeshes.
        std::array<float, 3> _bgColor{0.2f, 0.2f, 0.2f};

    private:

        void executeStack(const py::dict& stack, const py::list& events);

        ///< (Re)build a single input from its stack subtree (Create + Apply entries),
        ///< replacing _inputs[idx] in place. Used by both full and incremental rebuilds.
        ///< When reuseExisting is true and _inputs[idx]'s Create entry is unchanged, the
        ///< existing AInput is kept alive (skipping its — possibly expensive — constructor,
        ///< e.g. Image/Video file I/O) and only its modification state is reset + replayed.
        void rebuildInput(size_t idx, const py::dict& inputData, bool reuseExisting);

        ///< Per-input snapshot of the Python stack dict from the last reload — diffed against
        ///< the freshly-executed stack via Python equality so reloadSourceFile() only rebuilds
        ///< inputs that changed, without paying a full pyToJson pass on every reload.
        py::dict _pySnapshot{};

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
        ///< Ambient-clock pause spans from Wait events' `stop` lists — see
        ///< ClockStops (AInput.hpp) and the Wait branch in executeStack.
        ClockStops _clockStops{};

        ///< Timestamps:
        std::map<size_t, std::string> _timestamps{};

        ///< Frame we last jumped to via goToPrevTimestamp/goToNextTimestamp,
        ///< and when. Used to skip past it only on a quick double-press (< 2s).
        size_t                                        _lastJumpedFrame{0};
        std::chrono::steady_clock::time_point         _lastJumpTime{};

        ///< Inputs created
        std::vector<std::unique_ptr<IInput>> _inputs{};
    };
};
