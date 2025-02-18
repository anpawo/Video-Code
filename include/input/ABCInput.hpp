/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Input
*/

#pragma once

#include <vector>

#include "input/IInput.hpp"
#include "opencv2/core/mat.hpp"

class ABCInput : public IInput
{
public:

    ABCInput() = default;
    virtual ~ABCInput() = default;

    ///< Deep copy of `_frames`
    IInput* copy() final;

    std::vector<cv::Mat>& getFrames() final;

protected:

    std::vector<cv::Mat> _frames{}; ///< Frames of the Input
};
