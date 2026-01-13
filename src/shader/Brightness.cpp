/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Brightness
*/

#include <opencv2/core.hpp>
#include <opencv2/opencv.hpp>

#include "shader/ShaderFactory.hpp"

void Brightness::render(cv::Mat& mat, size_t) const
{
    int beta = static_cast<int>(_args.at("amount"));

    if (beta == 0) {
        return;
    }

    mat.convertTo(mat, -1, 1.0, beta);
}
