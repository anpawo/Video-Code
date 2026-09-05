/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Compiler
*/

#pragma once

#include <opencv2/opencv.hpp>

#include "core/Config.hpp"
#include "core/Core.hpp"

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

        ///< Renders the still at `first` — or, with --sheet, that many
        ///< moments of [first, last] side by side — into `config.outputFile`.
        int generateImage(VulkanHeadlessRenderer& renderer, size_t first, size_t last);

        Config config;

        ///< Core handling the images
        Core _core;
    };
};
