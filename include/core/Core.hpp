/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Core
*/

#pragma once

#include <pybind11/pybind11.h>
#include <vulkan/vulkan.h>

#include <array>
#include <chrono>
#include <functional>
#include <map>
#include <memory>
#include <opencv2/opencv.hpp>
#include <utility>

#include "core/Config.hpp"
#include "input/AInput.hpp" // ClockStops
#include "input/IInput.hpp"

namespace py = pybind11;

// argparse is a COMMAND-LINE parser, and it was reaching five headers through
// this one — 1381 of the 1754 include events of a 75-line ScreenSize.cpp. Every
// use here is by reference, so a forward declaration is all a header needs; the
// definition belongs to the .cpp files that actually read a flag.
namespace argparse
{
    class ArgumentParser;
}

namespace VC
{
    class VulkanWidget; // forward declaration for uploadTextures

    class Core
    {
    public:

        Core(const argparse::ArgumentParser& parser, const Config& config);

        ///< The editor's constructor: no command line to read.  `--showstack`
        ///< and `--showtimeline` are the only things the parser was ever asked
        ///< for here, and neither means anything in a window with a timeline of
        ///< its own.  Does NOT execute the scene — see rebuildFromContext().
        explicit Core(const Config& config);
        ~Core() = default;

        ///< Reload the source file, then execute the stack, then add the new frames to the Timeline.
        void reloadSourceFile();

        ///< Rebuild from the Context the CALLER has already populated.
        ///
        ///< The editor executes the buffer itself (serialize.execSource) so that
        ///< what runs is what is on screen rather than what is on disk. Running
        ///< it a second time here would be a second execution of arbitrary user
        ///< code with side effects, and the two could disagree — so this reads
        ///< the stack that execution left behind and does the rest.
        void rebuildFromContext();

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

        //: Whether the last attempt to run the scene threw. The editor keeps
        //: going on a broken edit — that is the point of the catch, it leaves
        //: the last good render on screen — but a batch render must not encode
        //: zero frames, print a green tick and exit 0, which is what it did.
        bool _sceneFailed{false};

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

        ///< Boxes for ShaderSpace::Anchor, keyed (input index, fillShaderSince).
        ///< A PURE CACHE, not remembered state: the value is a function of a
        ///< declared frame, so re-deriving it always gives the same box —
        ///< which is what keeps a pinned pattern stable under preview
        ///< scrubbing and hot-reload resume, where "the first box actually
        ///< rendered" would depend on render history. Only the cost is saved
        ///< (an anchored paint would otherwise re-tessellate its host every
        ///< frame); cleared on reload, where the geometry itself may change.
        std::map<std::pair<size_t, size_t>, ShaderBox> _anchorBoxes{};

        ///< The host's box at `since`, re-derived through the normal
        ///< metadata → mesh path and memoised.
        const ShaderBox& anchorBoxFor(size_t inputIndex, size_t since);

        ///< The scene's camera at a given frame, or the identity when no
        ///< scene input is one. Found by a scan rather than remembered: the
        ///< input set is rebuilt on every reload, and a stale index there
        ///< would point the camera at whatever took its slot.
        Camera2D cameraAt(size_t frame) const;

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
        size_t                                _lastJumpedFrame{0};
        std::chrono::steady_clock::time_point _lastJumpTime{};

        ///< Inputs created
        std::vector<std::unique_ptr<IInput>> _inputs{};
    };
};
