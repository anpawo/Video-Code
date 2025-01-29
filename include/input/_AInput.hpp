/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Input
*/

#pragma once

#include <vector>

#include "input/_IInput.hpp"
#include "opencv2/core/mat.hpp"

class _AInput : public _IInput {
public:

    _AInput(std::vector<cv::Mat>&& frames);
    virtual ~_AInput() = default;

    const std::vector<cv::Mat>& getFrames() final;
    std::vector<cv::Mat>& getFramesForTransformation() final;
    void concat(std::shared_ptr<_IInput> other) final;

private:

    /**
     * @ frames of the input
     * - a single frame for an image
     * - a list of frame for a video
     */
    std::vector<cv::Mat> _frames{};
};
