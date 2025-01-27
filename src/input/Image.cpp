/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Image
*/

#include "input/Image.hpp"

#include <opencv2/core/mat.hpp>
#include <opencv2/imgcodecs.hpp>
#include <utility>
#include <vector>

#include "utils/Exception.hpp"

static std::vector<cv::Mat> loadFrames(const std::string& inputName)
{
    cv::Mat image = cv::imread(inputName);

    if (image.empty()) {
        throw Error("Invalid Image: " + inputName);
    }

    return {image};
}

Image::Image(std::string&& inputName)
    : _AInput(loadFrames(inputName))
    , _inputName(std::forward<std::string&&>(inputName))
{
}
