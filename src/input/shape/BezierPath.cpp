/*
** EPITECH PROJECT, 2026
** video-code
** File description:
** BezierPath
*/

#include "input/shape/BezierPath.hpp"

#include <mapbox/earcut.hpp>

#include "vulkan/MeshFactory.hpp"
#include "utils/Logger.hpp"

#ifdef VC_DEBUG_ON
#  include <chrono>
#  define BP_T(name)  auto name = std::chrono::high_resolution_clock::now()
#  define BP_US(a, b) std::chrono::duration_cast<std::chrono::microseconds>((b) - (a)).count()
#else
#  define BP_T(name)  [[maybe_unused]] int name = 0
#  define BP_US(a, b) 0L
#endif

BezierPath::BezierPath(json::object_t&& args)
    : AInput(std::move(args))
{
}

Mesh BezierPath::getMesh(const Metadata& meta, const Config& config)
{
    BP_T(t0);

    _points.clear();
    buildPath(meta.args);

    BP_T(t1);

    size_t n = _points.size();
    if (n < 4 || n % 2 != 0) {
        return {};
    }

    // Build quadratic bezier segments from the anchor-handle path.
    size_t                         segCount = n / 2;
    std::vector<QuadraticBezier2D> curves;
    curves.reserve(segCount);
    for (size_t i = 0; i < segCount; ++i) {
        curves.push_back({
            _points[2 * i],
            _points[2 * i + 1],
            _points[(2 * i + 2) % n],
        });
    }

    // Bounding box of control points.
    float minX = _points[0][0], maxX = _points[0][0];
    float minY = _points[0][1], maxY = _points[0][1];
    for (const auto& p : _points) {
        minX = std::min(minX, p[0]);
        maxX = std::max(maxX, p[0]);
        minY = std::min(minY, p[1]);
        maxY = std::max(maxY, p[1]);
    }

    // Shift all control points so the bounding box starts at (0,0).
    cv::Vec2f offset{-minX, -minY};
    for (auto& c : curves) {
        c.p0 += offset;
        c.p1 += offset;
        c.p2 += offset;
    }

    MeshFactory factory({maxX - minX, maxY - minY}, meta, config);

    // Apply meta.opacity to both colors.
    float     opacityF = meta.opacity / 255.f;
    cv::Vec4b fillColor = _fillColor;
    cv::Vec4b strokeColor = _strokeColor;
    fillColor[3] = static_cast<uint8_t>(fillColor[3] * opacityF);
    strokeColor[3] = static_cast<uint8_t>(strokeColor[3] * opacityF);

    bool hasStroke = (_strokeWidth > 0.f && strokeColor[3] > 0);

    // Sample the bezier path to a local-space polyline for fill tessellation.
    BP_T(t2);
    std::vector<cv::Vec2f> poly;
    if (fillColor[3] > 0) {
        for (size_t ci = 0; ci < curves.size(); ++ci) {
            int steps = factory.quadraticStrokeSteps(curves[ci]);
            int sStart = (ci == 0) ? 0 : 1;
            int sEnd = (_closed && ci == curves.size() - 1) ? steps - 1 : steps;
            for (int s = sStart; s <= sEnd; ++s) {
                float t = static_cast<float>(s) / static_cast<float>(steps);
                poly.push_back(MeshFactory::evalQuadratic(curves[ci], t));
            }
        }
    }

    // Fill triangulation — earcut handles non-convex polygons correctly.
    BP_T(t3);
    if (fillColor[3] > 0 && poly.size() >= 3) {
        std::vector<std::vector<std::array<float, 2>>> polygon(1);
        polygon[0].reserve(poly.size());
        for (const auto& p : poly)
            polygon[0].push_back({p[0], p[1]});

        auto earIndices = mapbox::earcut<uint16_t>(polygon);

        uint16_t firstPolyIdx = factory.vertexCount();
        for (const auto& p : poly)
            factory.addVertex(p[0], p[1], fillColor);

        for (auto idx : earIndices)
            factory.mesh.indices.push_back(firstPolyIdx + idx);
    }

    // Stroke rendered on top of fill, extruded inward so it stays within the boundary.
    BP_T(t4);
    if (hasStroke) {
        factory.addQuadraticStrokePath(curves, _strokeWidth, strokeColor, _closed, _closed);
    }
    BP_T(t5);

    if (BP_US(t0, t5) > 400)
        VC_LOG(std::format(
            "[bezier] buildPath:{}µs  curves:{}µs  sample:{}µs  earcut:{}µs  stroke:{}µs  pts:{}\n",
            BP_US(t0, t1), BP_US(t1, t2), BP_US(t2, t3), BP_US(t3, t4), BP_US(t4, t5), n));

    return factory.generateMesh();
}
