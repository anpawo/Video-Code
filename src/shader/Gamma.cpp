/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** GammaCorrection
*/

#include <opencv2/core.hpp>
#include <opencv2/opencv.hpp>

#include "shader/ShaderFactory.hpp"

void Gamma::render(cv::Mat& mat, size_t) const
{
    double gamma = _args.at("gamma");

    if (gamma <= 0.0) {
        gamma = 1.0; // no correction
    }

    const double invGamma = 1.0 / gamma;

    cv::Mat lut(1, 256, CV_8UC1);
    for (int i = 0; i < 256; ++i) {
        const double normalized = i / 255.0;

        lut.at<uchar>(i) = cv::saturate_cast<uchar>(std::pow(normalized, invGamma) * 255.0);
    }

    cv::LUT(mat, lut, mat);
}
