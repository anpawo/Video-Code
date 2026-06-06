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

        ///< Update the current frame by generating the meshes.
        std::vector<Mesh> generateMeshes();

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

        void executeStack(const py::list& stack);

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
