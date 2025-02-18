/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Input
*/

#pragma once

#include <vector>

#include "opencv2/core/mat.hpp"

class IInput
{
public:

    IInput() = default;
    virtual ~IInput() = default;

    ///< Deep copy of `_frames`
    virtual IInput* copy() = 0;

    ///< Get the frames
    virtual std::vector<cv::Mat>& getFrames() = 0;
};
