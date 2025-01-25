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

Image::Image(std::string&& inputName)
    : _AInput(std::forward<std::string&&>(inputName), loadFrames(inputName))
{
}

std::vector<cv::Mat> Image::loadFrames(const std::string& inputName)
{
    cv::Mat image = cv::imread(inputName);

    if (image.empty()) {
        throw Error("Invalid Image: " + inputName);
    }

    return {image};
}
