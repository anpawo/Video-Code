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

class ABCConcreteInput : public IInput
{
public:

    ABCConcreteInput() = default;
    ABCConcreteInput(std::vector<cv::Mat>&& frames);
    ~ABCConcreteInput() = default;

    ///< Deep copy of `_frames`
    IInput* copy() final;

    ///< Iteration
    std::vector<cv::Mat>::iterator begin() final;
    std::vector<cv::Mat>::iterator end() final;

    ///< Size
    size_t size() final;

protected:

    std::vector<cv::Mat> _frames{}; ///< Frames of the Input
};
