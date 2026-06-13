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

void Polygon::buildPath(const Metadata& meta)
{
    const auto& args = meta.args();

    _strokeWidth = args.at("strokeWidth").get<float>() * config::worldToPixelRatio;
    parseColorOrGradient(args, "fillColor",   _fillColor,   _fillStops,   _fillGradType,   _fillGradientAngle);
    parseColorOrGradient(args, "strokeColor", _strokeColor, _strokeStops, _strokeGradType, _strokeGradientAngle);
    // Open paths (Curve, …): stroke only, no closing segment, and the points
    // keep their absolute coordinates (no bbox normalization in getMesh).
    _closed = !(args.contains("open") && args.at("open").get<bool>());

    // Multi-contour shapes (letter glyphs): point count per contour.
    _contourSizes = meta.contourSizesPtr ? *meta.contourSizesPtr : std::vector<size_t>{};

    const auto& points = meta.pointsPtr ? *meta.pointsPtr : std::vector<cv::Vec2f>{};
    int n = static_cast<int>(points.size());
    if (n < 4 || n % 2 != 0)
        return;

    _points = points;
}
