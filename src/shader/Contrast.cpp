/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** contrast
*/

#include <algorithm>
#include <opencv2/core.hpp>
#include <opencv2/opencv.hpp>

#include "shader/ShaderFactory.hpp"

void Contrast::render(cv::Mat& mat, size_t) const
{
    int value = _args.at("value");

    if (value == 0) {
        return;
    }

    if (value < -255) value = -255;
    if (value > 255) value = 255;

    double factor = (259.0 * (value + 255.0)) / (255.0 * (259.0 - value));

    cv::Mat mat16;
    mat.convertTo(mat16, CV_16SC4);

    for (int y = 0; y < mat16.rows; ++y) {
        auto* row = mat16.ptr<cv::Vec<short, 4>>(y);
        for (int x = 0; x < mat16.cols; ++x) {
            for (int c = 0; c < 3; ++c) {
                int v = static_cast<int>(factor * (row[x][c] - 128) + 128);
                row[x][c] = static_cast<short>(std::clamp(v, 0, 255));
            }
        }
    }

    mat16.convertTo(mat, CV_8UC4);
}
