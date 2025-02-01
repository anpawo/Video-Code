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
     * @ return a const ref to the frames
     */
    virtual const std::vector<cv::Mat>& cgetFrames() = 0;

    /**
     * @ return a ref to the frames
     */
    virtual std::vector<cv::Mat>& getFrames() = 0;

    /**
     * @ concat other after self
     */
    virtual void concat(std::shared_ptr<_IInput> other) = 0;

    /**
     * @ update the current frames
     */
    virtual void setFrames(std::vector<cv::Mat>&& frames) = 0;

private:
};
