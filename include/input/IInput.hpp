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

    ///< Iteration
    virtual std::vector<cv::Mat>::iterator begin() = 0;
    virtual std::vector<cv::Mat>::iterator end() = 0;

    ///< Size
    virtual size_t size() = 0;
};
