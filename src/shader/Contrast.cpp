/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Contrast
*/

#include <opencv2/core.hpp>
#include <opencv2/opencv.hpp>

#include "shader/ShaderFactory.hpp"

void Contrast::render(cv::Mat& mat, size_t) const
{
    int amount = static_cast<int>(_args.at("amount"));

    if (amount == 0) {
        return;
    }

    if (amount < -255) {
        amount = -255;
    }
    if (amount > 255) {
        amount = 255;
    }

    const double alpha = (259.0 * (amount + 255.0)) / (255.0 * (259.0 - amount));
    const double beta = 128.0 * (1.0 - alpha);

    mat.convertTo(mat, -1, alpha, beta);
}
