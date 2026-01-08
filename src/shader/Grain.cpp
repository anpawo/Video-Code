/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** grain
*/

#include <algorithm>
#include <cmath>
#include <opencv2/core.hpp>
#include <opencv2/opencv.hpp>

#include "shader/ShaderFactory.hpp"

void Grain::render(cv::Mat& mat, size_t) const
{
    double amount = _args.at("amount");

    if (amount < 0.0) amount = 0.0;
    if (amount > 1.0) amount = 1.0;

    cv::Mat mat16;
    mat.convertTo(mat16, CV_16SC4);

    // Use monochrome noise for a film-like grain (avoid RGB speckles).
    cv::Mat noise(mat.size(), CV_32F);
    cv::randn(noise, 0.0, amount * 128.0);
    cv::GaussianBlur(noise, noise, cv::Size(3, 3), 0.0);

    for (int y = 0; y < mat16.rows; ++y) {
        auto* row = mat16.ptr<cv::Vec<short, 4>>(y);
        const auto* nrow = noise.ptr<float>(y);
        for (int x = 0; x < mat16.cols; ++x) {
            float n = nrow[x];
            float luma = 0.299f * row[x][2] + 0.587f * row[x][1] + 0.114f * row[x][0];
            float factor = 1.0f - std::abs(luma - 128.0f) / 128.0f;
            factor = std::clamp(factor, 0.0f, 1.0f);
            for (int c = 0; c < 3; ++c) {
                int v = row[x][c] + static_cast<int>(n * factor);
                row[x][c] = static_cast<short>(std::clamp(v, 0, 255));
            }
        }
    }

    mat16.convertTo(mat, CV_8UC4);
}
