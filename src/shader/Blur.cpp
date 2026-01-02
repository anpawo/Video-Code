/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** blur
*/

#include <opencv2/core.hpp>
#include <opencv2/opencv.hpp>

#include "effect/ShaderFactory.hpp"

void Blur::render(cv::Mat& mat, size_t) const
{
    size_t strength = _args.at("strength");

    if (strength < 1) {
        strength = 1;
    }
    if (strength % 2 == 0) {
        strength++;
    }

    cv::GaussianBlur(mat, mat, cv::Size(strength, strength), 0);
}
