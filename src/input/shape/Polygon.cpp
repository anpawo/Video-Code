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
    parseColorOrGradient(args, "fillColor",   _fillColor,   _fillStops,   _fillGradType,   _fillGradientAngle);
    parseColorOrGradient(args, "strokeColor", _strokeColor, _strokeStops, _strokeGradType, _strokeGradientAngle);
    // Open paths (Curve, …): stroke only, no closing segment, and the points
    // keep their absolute coordinates (no bbox normalization in getMesh).
    _closed = !(args.contains("open") && args.at("open").get<bool>());

    // Multi-contour shapes (letter glyphs): point count per contour.
    _contourSizes.clear();
    if (args.contains("contourSizes"))
        for (const auto& s : args.at("contourSizes"))
            _contourSizes.push_back(s.get<size_t>());

    int n = static_cast<int>(raw.size());
    if (n < 4 || n % 2 != 0)
        return;

    for (int i = 0; i < n; ++i)
        _points.push_back({
            raw[i][0] * config::worldToPixelRatio,
            -raw[i][1] * config::worldToPixelRatio,
        });
}
