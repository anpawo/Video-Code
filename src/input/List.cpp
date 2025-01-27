/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Image
*/

#include "input/List.hpp"

#include <opencv2/imgcodecs.hpp>
#include <vector>

#include "opencv2/core/mat.hpp"

static std::vector<cv::Mat> replicateFrame(std::shared_ptr<_IInput> frames, int n)
{
    std::vector<cv::Mat> result{};

    while (n--) {
        const auto& temp = frames->getFrames();
        result.insert(result.end(), temp.begin(), temp.end());
    }
    return result;
}

List::List(std::shared_ptr<_IInput> frames, int n)
    : _AInput(replicateFrame(frames, n))
{
}
