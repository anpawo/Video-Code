/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** gammaCorrection
*/

#include <opencv2/core.hpp>
#include <opencv2/opencv.hpp>

#include "shader/ShaderFactory.hpp"

void GammaCorrection::render(cv::Mat& mat, size_t) const
{
    double gammaCorrection = _args.at("gammaCorrection");

    if (gammaCorrection <= 0.0) gammaCorrection = 1.0;

    cv::Mat lut(1, 256, CV_8UC1);
    for (int i = 0; i < 256; ++i) {
        lut.at<uchar>(i) = cv::saturate_cast<uchar>(
            std::pow(i / 255.0, gammaCorrection) * 255.0
        );
    }
    cv::LUT(mat, lut, mat);
}
