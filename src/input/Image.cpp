/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Image
*/

#include "input/media/Image.hpp"

#include <opencv2/core/mat.hpp>
#include <opencv2/imgcodecs.hpp>
#include <vector>

#include "opencv2/imgproc.hpp"
#include "utils/Exception.hpp"

Image::Image(const std::string& inputName)
    : _inputName(inputName)
{
    cv::Mat image = cv::imread(inputName);

    if (image.empty())
    {
        throw Error("Could not load Image: " + inputName);
    }

    if (image.channels() != 4)
    {
        cv::cvtColor(image, image, cv::COLOR_BGR2BGRA);
    }

    _frames = {image};
}

///< After lots of tests, I feel like opencv crashs with the handling of RGBA.
///< So I'll keep them BGRA until the last second which is the display.
