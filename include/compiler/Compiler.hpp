/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Compiler
*/

#pragma once

#include <argparse/argparse.hpp>
#include <opencv2/opencv.hpp>

#include "core/Config.hpp"
#include "core/Core.hpp"

namespace VC
{
    class VulkanHeadlessRenderer; // forward declaration for generateImage

    class Compiler
    {
    public:

        Compiler(const argparse::ArgumentParser& parser);
        ~Compiler();

        ///< Generates a video, or — when `config.outputFile` has an image
        ///< extension (.png, .jpg/.jpeg, .bmp, .tiff/.tif, .webp) — a single
        ///< still frame instead.
        int generateVideo();

    private:

        ///< Renders a single frame and writes it to `config.outputFile`.
        int generateImage(VulkanHeadlessRenderer& renderer);

        Config config;

        ///< Core handling the images
        Core _core;
    };
};
