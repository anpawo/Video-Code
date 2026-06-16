/*
** EPITECH PROJECT, 2026
** video-code
** File description:
** Color
*/

#pragma once

#include <cstdint>
#include <opencv2/core/matx.hpp>
#include <vector>

inline cv::Vec4b lerpColor(const cv::Vec4b& a, const cv::Vec4b& b, float t)
{
    return cv::Vec4b(
        static_cast<uint8_t>(a[0] + (b[0] - a[0]) * t),
        static_cast<uint8_t>(a[1] + (b[1] - a[1]) * t),
        static_cast<uint8_t>(a[2] + (b[2] - a[2]) * t),
        static_cast<uint8_t>(a[3] + (b[3] - a[3]) * t)
    );
}

// One color "breakpoint" in a multi-stop gradient — `position` is normalized
// to [0, 1] (CSS percent / 100), and stops are kept sorted by position.
struct GradientStop
{
    cv::Vec4b color;
    float     position;
};

// Resolves the color at `t` (normalized projection along the gradient axis,
// typically in [0, 1]) by finding the bracketing pair of stops and lerping
// between them — generalizes a 2-color lerp to N color breakpoints, mirroring
// how CSS linear-gradient() interpolates between consecutive color-stops.
inline cv::Vec4b lerpGradient(const std::vector<GradientStop>& stops, float t)
{
    if (stops.size() == 1 || t <= stops.front().position)
        return stops.front().color;
    if (t >= stops.back().position)
        return stops.back().color;

    for (size_t i = 1; i < stops.size(); ++i) {
        if (t <= stops[i].position) {
            float span = stops[i].position - stops[i - 1].position;
            float localT = (span > 0.f) ? (t - stops[i - 1].position) / span : 0.f;
            return lerpColor(stops[i - 1].color, stops[i].color, localT);
        }
    }
    return stops.back().color;
}
