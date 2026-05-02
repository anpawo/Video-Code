/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Polygon
*/

#include "input/shape/Polygon.hpp"

Polygon::Polygon(json::object_t&& args)
    : BezierPath(std::move(args))
{
}

void Polygon::buildPath(const json::object_t& args)
{
    auto raw = args.at("points").get<std::vector<std::vector<float>>>();
    _strokeWidth = args.at("strokeWidth").get<float>() * config::worldToPixelRatio;
    _fillColor = colorFromJson(args.at("fillColor"), 255);
    _strokeColor = colorFromJson(args.at("strokeColor"), 255);
    _closed = true;

    int n = static_cast<int>(raw.size());
    if (n < 4 || n % 2 != 0)
        return;

    for (int i = 0; i < n; ++i)
        _points.push_back({
            raw[i][0] * config::worldToPixelRatio,
            -raw[i][1] * config::worldToPixelRatio,
        });
}
