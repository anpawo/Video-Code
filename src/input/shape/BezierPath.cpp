/*
** EPITECH PROJECT, 2026
** video-code
** File description:
** BezierPath
*/

#include "input/shape/BezierPath.hpp"

#include "vulkan/MeshFactory.hpp"

BezierPath::BezierPath(json::object_t&& args)
    : AInput(std::move(args))
{
}

Mesh BezierPath::getMesh(const Metadata& meta, const Config& config)
{
    _points.clear();
    buildPath(meta.args);

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
    float     opacityF    = meta.opacity / 255.f;
    cv::Vec4b fillColor   = _fillColor;
    cv::Vec4b strokeColor = _strokeColor;
    fillColor[3]   = static_cast<uint8_t>(fillColor[3] * opacityF);
    strokeColor[3] = static_cast<uint8_t>(strokeColor[3] * opacityF);

    bool hasStroke    = (_strokeWidth > 0.f && strokeColor[3] > 0);
    // For closed shapes with a stroke, the stroke sits inside the boundary and
    // the fill is shrunk inward so they never overlap.
    bool insideStroke = _closed && hasStroke;

    // Sample the bezier path to a local-space polyline for fill tessellation.
    std::vector<cv::Vec2f> poly;
    if (fillColor[3] > 0 || insideStroke) {
        for (size_t ci = 0; ci < curves.size(); ++ci) {
            int steps  = factory.quadraticStrokeSteps(curves[ci]);
            int sStart = (ci == 0) ? 0 : 1;
            int sEnd   = (_closed && ci == curves.size() - 1) ? steps - 1 : steps;
            for (int s = sStart; s <= sEnd; ++s) {
                float t = static_cast<float>(s) / static_cast<float>(steps);
                poly.push_back(MeshFactory::evalQuadratic(curves[ci], t));
            }
        }
    }

    // Fill triangulation.
    if (fillColor[3] > 0 && poly.size() >= 3) {
        if (insideStroke) {
            // Convert to world space and inset by strokeWidth so the fill doesn't
            // reach the shape boundary — the stroke will occupy that band.
            std::vector<cv::Vec2f> worldPoly;
            worldPoly.reserve(poly.size());
            for (const auto& p : poly)
                worldPoly.push_back(factory.toWorldPoint(p[0], p[1]));

            float worldStrokeW = std::hypot(factory.M(0, 0), factory.M(1, 0)) * _strokeWidth;
            std::vector<cv::Vec2f> insetPoly =
                MeshFactory::insetPolyWorld(worldPoly, worldStrokeW, _closed);

            if (insetPoly.size() >= 3) {
                cv::Vec2f centroid{0.f, 0.f};
                for (const auto& p : insetPoly) centroid += p;
                centroid *= (1.f / static_cast<float>(insetPoly.size()));

                uint16_t centerIdx = factory.vertexCount();
                factory.addWorldVertex(centroid[0], centroid[1], fillColor);

                uint16_t firstIdx = factory.vertexCount();
                for (const auto& p : insetPoly)
                    factory.addWorldVertex(p[0], p[1], fillColor);

                size_t sz = insetPoly.size();
                for (size_t i = 0; i < sz; ++i) {
                    factory.mesh.indices.push_back(centerIdx);
                    factory.mesh.indices.push_back(firstIdx + static_cast<uint16_t>(i));
                    factory.mesh.indices.push_back(firstIdx + static_cast<uint16_t>((i + 1) % sz));
                }
            }
        } else {
            // No stroke (or open path): fill takes the full shape boundary.
            cv::Vec2f centroid{0.f, 0.f};
            for (const auto& p : poly) centroid += p;
            centroid *= (1.f / static_cast<float>(poly.size()));

            uint16_t centerIdx = factory.vertexCount();
            factory.addVertex(centroid[0], centroid[1], fillColor);

            uint16_t firstPolyIdx = factory.vertexCount();
            for (const auto& p : poly)
                factory.addVertex(p[0], p[1], fillColor);

            size_t polySize = poly.size();
            for (size_t i = 0; i < polySize; ++i) {
                factory.mesh.indices.push_back(centerIdx);
                factory.mesh.indices.push_back(firstPolyIdx + static_cast<uint16_t>(i));
                factory.mesh.indices.push_back(firstPolyIdx + static_cast<uint16_t>((i + 1) % polySize));
            }
        }
    }

    // Stroke along the original boundary, extruded inward for closed shapes.
    if (hasStroke) {
        factory.addQuadraticStrokePath(curves, _strokeWidth, strokeColor, _closed, insideStroke);
    }

    return factory.generateMesh();
}
