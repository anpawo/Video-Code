/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Image
*/

#include "input/_AInput.hpp"

#include <opencv2/core/mat.hpp>
#include <opencv2/imgcodecs.hpp>
#include <vector>

_AInput::_AInput(std::vector<cv::Mat>&& frames)
    : _frames(std::forward<std::vector<cv::Mat>&&>(frames))
{
}

const std::vector<cv::Mat>& _AInput::getFrames()
{
    return _frames;
}

std::vector<cv::Mat>& _AInput::getFramesForTransformation()
{
    return _frames;
}

void _AInput::concat(std::shared_ptr<_IInput> other)
{
    _frames.insert(_frames.end(), other->getFrames().cbegin(), other->getFrames().cend());
}
