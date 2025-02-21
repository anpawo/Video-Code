/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Compiler
*/

#pragma once

#include <vector>

#include "opencv2/core/mat.hpp"

namespace Compiler::Writer
{
    int generateVideo(
        int width,
        int height,
        int fps,
        std::string filename,
        const std::vector<cv::Mat> &frames
    );
};
