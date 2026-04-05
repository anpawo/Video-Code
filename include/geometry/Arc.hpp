/*
** EPITECH PROJECT, 2026
** video-code
** File description:
** Arc
*/

#pragma once

#include <cmath>
#include <opencv2/core/types.hpp>
#include <vector>

// Returns n+1 points along a circular arc.
// cx, cy : center in local space
// r      : radius
// start  : start angle in radians
// end    : end angle in radians
// n      : number of segments
inline std::vector<cv::Vec2f> arcPoints(float cx, float cy, float r, float start, float end, int n)
{
    std::vector<cv::Vec2f> pts;
    pts.reserve(n + 1);
    for (int i = 0; i <= n; i++) {
        float t     = static_cast<float>(i) / static_cast<float>(n);
        float angle = start + t * (end - start);
        pts.push_back({cx + r * std::cos(angle), cy + r * std::sin(angle)});
    }
    return pts;
}
