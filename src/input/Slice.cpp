/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Slice
*/

#include "input/Slice.hpp"

#include "input/_AInput.hpp"

static std::vector<cv::Mat> loadFrames(std::shared_ptr<_IInput> src, int lowerBound, int upperBound)
{
    const auto &srcFrame = src->cgetFrames();

    if (upperBound < 0) {
        upperBound = srcFrame.size() + upperBound;
    }

    return {srcFrame.begin() + lowerBound, srcFrame.begin() + upperBound + 1};
}

Slice::Slice(std::shared_ptr<_IInput> src, int lowerBound, int upperBound)
    : _AInput(loadFrames(src, lowerBound, upperBound))
    , _src(src)
    , _lowerBound(lowerBound)
    , _upperBound(upperBound)
{
}
