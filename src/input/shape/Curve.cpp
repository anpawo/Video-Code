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
    const auto& args = meta.args();
    const auto& pts = args.at("points");
    if (pts.size() < 2) {
        return {};
    }

    float     strokeWidth = args.at("strokeWidth").get<float>() * config::worldToPixelRatio;
    cv::Vec4b strokeColor = colorFromJson(args.at("strokeColor"), meta.opacity);

    if (strokeColor[3] == 0 || strokeWidth <= 0.f) {
        return {};
    }

    std::vector<cv::Vec2f> points;
    points.reserve(pts.size());
    for (const auto& p : pts) {
        points.push_back({
            p[0].get<float>() * config::worldToPixelRatio,
            -p[1].get<float>() * config::worldToPixelRatio,
        });
    }

    size_t                         N = points.size();
    std::vector<QuadraticBezier2D> curves;
    curves.reserve(N - 1);
    for (size_t i = 0; i + 1 < N; ++i) {
        cv::Vec2f mid = (points[i] + points[i + 1]) * 0.5f;
        curves.push_back({points[i], mid, points[i + 1]});
    }

    // No offset — pass a dummy local size; M will handle world placement.
    // localSize just needs to be non-zero; (0,0) is fine if MeshFactory
    // doesn't use it for anything other than the transform.
    MeshFactory factory({0.f, 0.f}, meta, config);
    factory.addQuadraticStrokePath(curves, strokeWidth, strokeColor, false);
    return factory.generateMesh();
}
