/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Image
*/

#include "input/List.hpp"

#include <opencv2/imgcodecs.hpp>
#include <vector>

#include "input/_AInput.hpp"
#include "opencv2/core/mat.hpp"

static std::vector<cv::Mat> replicateFrame(std::shared_ptr<_IInput> input, int n)
{
    std::vector<cv::Mat> result{};

    while (n--)
    {
        const auto& temp = input->cgetFrames();
        result.insert(result.end(), temp.begin(), temp.end());
    }
    return result;
}

List::List(std::shared_ptr<_IInput> input, int n)
    : _AInput(replicateFrame(input, n))
{
}
