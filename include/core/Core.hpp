/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Core
*/

#pragma once

#include <argparse/argparse.hpp>
#include <functional>
#include <memory>
#include <opencv2/opencv.hpp>
#include <vulkan/vulkan.h>

#include "core/Config.hpp"
#include "input/IInput.hpp"

namespace VC
{
    class VulkanWidget; // forward declaration for uploadTextures

    class Core
    {
    public:

        Core(const argparse::ArgumentParser& parser, const Config& config);
        ~Core() = default;

        ///< Reload the source file, then execute the stack, then add the new frames to the Timeline.
        void        reloadSourceFile();
        std::string serializeScene();
        void        executeStack();

        ///< Update the current frame by generating the meshes.
        std::vector<Mesh> generateMeshes();

        ///< Upload textures for all Image inputs to a Vulkan renderer.
        ///< uploadFn receives each image's cv::Mat and returns the VkDescriptorSet.
        void uploadTextures(VulkanWidget* widget);
        void uploadTextures(std::function<VkDescriptorSet(const cv::Mat&)> uploadFn);

        ///< Time control
        void pause();
        void goToFirstFrame();
        void goToLastFrame();
        void forward1frame();
        void backward1frame();

        // ---

        ///< Index of the frame currently being displayed
        size_t _index{0};
        size_t _nbFrame{0}; // Starting at 1 forces the first frame to be generated even without any transformations.

        ///< Information display
        const bool _showstack;
        const bool _showtimeline;

    private:

        ///< Config (Window / Framerate / Paths)
        const Config& _config;

        ///< The video editor is paused
        bool _paused{false};
        bool _indexChanged{true};

        ///< Waits:
        std::map<size_t, size_t> _waits{};

        ///< Inputs created
        std::vector<std::unique_ptr<IInput>> _inputs{};

        ///< Stack containing the steps of the video
        json::array_t _stack{};
    };
};
