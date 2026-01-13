/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** grain
*/

#include <opencv2/core.hpp>
#include <opencv2/opencv.hpp>

#include "shader/ShaderFactory.hpp"

void Grain::render(cv::Mat& mat, size_t) const
{
    double amount = _args.at("amount");
    if (amount <= 0.0) {
        return;
    }
    if (amount > 1.0) {
        amount = 1.0;
    }

    // Bruit mono pour éviter le speckle couleur
    cv::Mat noise(mat.size(), CV_16SC1);
    cv::randn(noise, 0, static_cast<int>(amount * 64.0));

    for (int y = 0; y < mat.rows; ++y) {
        auto* row = mat.ptr<cv::Vec4b>(y);
        const short* nrow = noise.ptr<short>(y);

        for (int x = 0; x < mat.cols; ++x) {
            const int delta = nrow[x];

            row[x][0] = cv::saturate_cast<uchar>(row[x][0] + delta);
            row[x][1] = cv::saturate_cast<uchar>(row[x][1] + delta);
            row[x][2] = cv::saturate_cast<uchar>(row[x][2] + delta);
        }
    }
}
