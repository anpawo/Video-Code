/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** IInput
*/

#pragma once

#include <vector>

#include "opencv2/core/mat.hpp"

class _IInput {
public:

    _IInput() = default;
    virtual ~_IInput() = default;

    /**
     * @ return the loaded frames of the input
     * - used to push them on the timeline
     */
    virtual const std::vector<cv::Mat>& cgetFrames() = 0;
    virtual std::vector<cv::Mat>& getFrames() = 0;
    virtual void concat(std::shared_ptr<_IInput> other) = 0;

private:
};
