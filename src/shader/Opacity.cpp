/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** fade
*/
#include <opencv2/opencv.hpp>

#include "effect/ShaderFactory.hpp"
#include "opencv2/core/matx.hpp"

void Opacity::render(cv::Mat& mat, size_t) const
{
    size_t opacity = args.at("opacity");

    mat.forEach<cv::Vec4b>([opacity](cv::Vec4b& p, const int*) {
        if (p[3] != 0) {
            p[3] = opacity;
        }
    });
}
