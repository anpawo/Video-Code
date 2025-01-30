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

#include "opencv2/imgproc.hpp"
#include "utils/Exception.hpp"

static std::vector<cv::Mat> loadFrames(const std::string& inputName)
{
    cv::Mat frame = cv::imread(inputName);

    if (frame.empty()) {
        throw Error("Invalid Image: " + inputName);
    }

    if (frame.channels() == 3) {
        cv::cvtColor(frame, frame, cv::COLOR_BGR2BGRA);
    }

    return {frame};
}

Image::Image(std::string&& inputName)
    : _AInput(loadFrames(inputName))
    , _inputName(std::forward<std::string&&>(inputName))
{
}
