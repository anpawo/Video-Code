/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Sharpen
*/

#include <opencv2/core.hpp>
#include <opencv2/opencv.hpp>

#include "shader/ShaderFactory.hpp"

void Sharpen::render(cv::Mat& mat, size_t) const
{
    double amount = _args.at("amount");

    if (amount <= 0.0) {
        return;
    }
    if (amount > 1.0) {
        amount = 1.0;
    }

    cv::Mat original = mat.clone();
    cv::Mat sharpened;
    const cv::Mat kernel = (cv::Mat_<float>(3, 3) << 0, -1, 0, -1, 5, -1, 0, -1, 0);

    cv::filter2D(original, sharpened, original.depth(), kernel);
    cv::addWeighted(original, 1.0 - amount, sharpened, amount, 0.0, mat);
}
