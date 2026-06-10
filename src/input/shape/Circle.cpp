/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Circle
*/

#include "input/shape/Circle.hpp"

#include <cmath>

Circle::Circle(json::object_t&& args)
    : BezierPath(std::move(args))
{
}

// Approximate a circle with N quadratic bezier segments using Manim's formula:
// anchors lie on the circle; handles are the mid-arc point scaled outward by
// 1/cos(segAngle/2), which equals the tangent-intersection distance.
void Circle::buildPath(const json::object_t& args)
{
    float radius = args.at("radius").get<float>() * config::worldToPixelRatio;
    _strokeWidth = args.at("strokeWidth").get<float>() * config::worldToPixelRatio;
    parseColorOrGradient(args, "fillColor",   _fillColor,   _fillStops,   _fillGradType,   _fillGradientAngle);
    parseColorOrGradient(args, "strokeColor", _strokeColor, _strokeStops, _strokeGradType, _strokeGradientAngle);
    _closed = true;

    const int   N = 16;
    const float segAngle = 2.f * static_cast<float>(M_PI) / N; // 45°
    const float cosHalf = std::cos(segAngle / 2.f);            // cos(22.5°) ≈ 0.9239

    _points.clear();
    _points.reserve(N * 2);

    for (int i = 0; i < N; ++i) {
        float aAngle = i * segAngle;
        float hAngle = aAngle + segAngle / 2.f;
        _points.push_back(radius * cv::Vec2f{std::cos(aAngle), std::sin(aAngle)}); // not reversed
        _points.push_back((radius / cosHalf) * cv::Vec2f{std::cos(hAngle), std::sin(hAngle)});
    }
}
