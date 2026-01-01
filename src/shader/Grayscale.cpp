/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** grayscale
*/

#include <opencv2/core.hpp>
#include <opencv2/opencv.hpp>

#include "effect/ShaderFactory.hpp"

void Grayscale::render(cv::Mat& mat, size_t) const
{
    mat.forEach<cv::Vec4b>([](cv::Vec4b& p, const int*) {
        uchar gray = static_cast<uchar>(0.299 * p[2] + 0.587 * p[1] + 0.114 * p[0]);
        p[0] = p[1] = p[2] = gray;
    });
}
