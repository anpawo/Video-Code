/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Image
*/

#include "input/Copy.hpp"

#include <opencv2/imgcodecs.hpp>
#include <vector>

#include "opencv2/core/mat.hpp"

static std::vector<cv::Mat> copyInput(std::shared_ptr<_IInput> input)
{
    std::vector<cv::Mat> result{};

    for (auto &it : input->getFrames()) {
        result.push_back(it.clone());
    }

    return result;
}

Copy::Copy(std::shared_ptr<_IInput> input)
    : _AInput(copyInput(input))
{
}
