/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** sharpen
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

    if (amount > 5.0) amount = 5.0;

    cv::Mat blurred;
    cv::GaussianBlur(mat, blurred, cv::Size(0, 0), 1.0);
    cv::addWeighted(mat, 1.0 + amount, blurred, -amount, 0.0, mat);
}
