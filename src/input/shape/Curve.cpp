/*
** EPITECH PROJECT, 2026
** video-code
** File description:
** Curve
*/

#include "input/shape/Curve.hpp"

#include <opencv2/core/matx.hpp>
#include <vector>

#include "vulkan/MeshFactory.hpp"

Curve::Curve(json::object_t&& args)
    : AInput(std::move(args))
{
}

Mesh Curve::getMesh(const Metadata& meta, const Config& config)
{
    const auto& args = meta.args;

    const auto& pts = args.at("points");
    if (pts.size() < 2) {
        return {};
    }

    float     strokeWidth = args.at("strokeWidth").get<float>() * config::worldToPixelRatio;
    cv::Vec4b strokeColor = colorFromJson(args.at("strokeColor"), meta.opacity);

    if (strokeColor[3] == 0 || strokeWidth <= 0.f) {
        return {};
    }

    // Collect points
    std::vector<cv::Vec2f> points;
    points.reserve(pts.size());
    for (const auto& p : pts) {
        points.push_back({p[0].get<float>() * config::worldToPixelRatio, p[1].get<float>() * config::worldToPixelRatio});
    }

    // Build N-1 quadratic bezier segments.
    // Handle = midpoint between anchors (degenerate = straight line).
    // With enough sample points this renders as a smooth curve.
    size_t                         N = points.size();
    std::vector<QuadraticBezier2D> curves;
    curves.reserve(N - 1);
    for (size_t i = 0; i + 1 < N; ++i) {
        cv::Vec2f mid = (points[i] + points[i + 1]) * 0.5f;
        curves.push_back({points[i], mid, points[i + 1]});
    }

    // Bounding box to build a local MeshFactory.
    float minX = points[0][0], maxX = points[0][0];
    float minY = points[0][1], maxY = points[0][1];
    for (const auto& p : points) {
        minX = std::min(minX, p[0]);
        maxX = std::max(maxX, p[0]);
        minY = std::min(minY, p[1]);
        maxY = std::max(maxY, p[1]);
    }

    cv::Vec2f offset{-minX, -minY};
    for (auto& c : curves) {
        c.p0 += offset;
        c.p1 += offset;
        c.p2 += offset;
    }

    MeshFactory factory({maxX - minX, maxY - minY}, meta, config);
    factory.addQuadraticStrokePath(curves, strokeWidth, strokeColor, false);

    return factory.generateMesh();
}
