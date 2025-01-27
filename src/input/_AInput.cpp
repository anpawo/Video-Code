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

#include "utils/Exception.hpp"

_AInput::_AInput(std::string&& inputName, std::vector<cv::Mat>&& frames)

    : _inputName(std::forward<std::string&&>(inputName))
    , _frames(std::forward<std::vector<cv::Mat>&&>(frames))
{
}

const std::vector<cv::Mat>& _AInput::getFrames()
{
    return _frames;
}

std::vector<cv::Mat> _AInput::loadFrames(const std::string&)
{
    throw Error("Invalid loadFrames.");
}
