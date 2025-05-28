/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Compiler
*/

#pragma once

#include <argparse/argparse.hpp>
#include <opencv2/opencv.hpp>

#include "core/Core.hpp"

namespace VC
{
    class Compiler
    {
    public:

        Compiler(const argparse::ArgumentParser& parser);
        ~Compiler();

        int generateVideo();

    private:

        ///< Core handling the images
        Core _core;
    };
};
