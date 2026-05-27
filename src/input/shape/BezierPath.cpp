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

// FNV-1a 64-bit hash over raw bytes, chainable (pass previous hash as seed).
static size_t fnvHash(const void* data, size_t bytes, size_t h = 0xcbf29ce484222325ULL)
{
    constexpr size_t PRIME = 0x00000100000001B3ULL;
    const auto*      p     = static_cast<const uint8_t*>(data);
    for (size_t i = 0; i < bytes; ++i)
        h = (h ^ p[i]) * PRIME;
    return h;
}

Mesh BezierPath::getMesh(const Metadata& meta, const Config& config)
{
    BP_T(t0);

    // --- Fast path: skip buildPath entirely when args are known static ----------
    // meta.argsStatic is true when no "Args" VertexShader has ever fired for this
    // input, so _baseArgs (and therefore _points) can never have changed.
    if (!meta.argsStatic || !_geomValid) {
        _points.clear();
        buildPath(meta.args);
    }

    BP_T(t1);

    size_t n = _points.size();
    if (n < 4 || n % 2 != 0) {
        return {};
    }

    // --- Geometry cache --------------------------------------------------------
    // Key: _points bytes + scale.x/y + rotation.
    // quadraticStrokeSteps() depends on the R*S part of the transform matrix,
    // but is translation-invariant — scale+rotation are sufficient as cache key.
    size_t geomHash = fnvHash(_points.data(), n * sizeof(cv::Vec2f));
    geomHash = fnvHash(&meta.scale.x,   sizeof(float), geomHash);
    geomHash = fnvHash(&meta.scale.y,   sizeof(float), geomHash);
    geomHash = fnvHash(&meta.rotation,  sizeof(float), geomHash);

    if (!_geomValid || geomHash != _lastGeomHash) {
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
        cv::Vec2f localOffset{-minX, -minY};
        for (auto& c : curves) {
            c.p0 += localOffset;
            c.p1 += localOffset;
            c.p2 += localOffset;
        }

        cv::Size2f localSize{maxX - minX, maxY - minY};

        // Use a temporary factory just for step calculation (position doesn't
        // affect quadraticStrokeSteps, so meta.position is irrelevant here).
        MeshFactory sampleFactory(localSize, meta, config);

        // Sample the bezier path to a local-space polyline for fill tessellation.
        std::vector<cv::Vec2f> localPoly;
        if (_fillColor[3] > 0) {
            for (size_t ci = 0; ci < curves.size(); ++ci) {
                int steps  = sampleFactory.quadraticStrokeSteps(curves[ci]);
                int sStart = (ci == 0) ? 0 : 1;
                int sEnd   = (_closed && ci == curves.size() - 1) ? steps - 1 : steps;
                for (int s = sStart; s <= sEnd; ++s) {
                    float t = static_cast<float>(s) / static_cast<float>(steps);
                    localPoly.push_back(MeshFactory::evalQuadratic(curves[ci], t));
                }
            }
        }

        // Fill triangulation — earcut handles non-convex polygons correctly.
        std::vector<uint16_t> earIndices;
        if (_fillColor[3] > 0 && localPoly.size() >= 3) {
            std::vector<std::vector<std::array<float, 2>>> polygon(1);
            polygon[0].reserve(localPoly.size());
            for (const auto& p : localPoly)
                polygon[0].push_back({p[0], p[1]});
            earIndices = mapbox::earcut<uint16_t>(polygon);
        }

        // Store in cache.
        _geomCache = GeomCache{
            std::move(localPoly),
            std::move(earIndices),
            std::move(curves),
            localSize,
            _fillColor,
            _strokeColor,
            _strokeWidth,
            _fillColor[3] > 0,
        };
        _lastGeomHash = geomHash;
        _geomValid    = true;
    }

    BP_T(t2);

    // --- Mesh assembly from cached local geometry + current transform ----------
    MeshFactory factory(_geomCache.localSize, meta, config);

    // Apply meta.opacity to both colors.
    float     opacityF    = meta.opacity / 255.f;
    cv::Vec4b fillColor   = _geomCache.rawFillColor;
    cv::Vec4b strokeColor = _geomCache.rawStrokeColor;
    fillColor[3]   = static_cast<uint8_t>(fillColor[3]   * opacityF);
    strokeColor[3] = static_cast<uint8_t>(strokeColor[3] * opacityF);

    bool hasStroke = (_geomCache.strokeWidth > 0.f && strokeColor[3] > 0);

    // Emit fill vertices (applies current transform M to each local point).
    BP_T(t3);
    if (_geomCache.hasFill && fillColor[3] > 0 && !_geomCache.earIndices.empty()) {
        uint16_t firstPolyIdx = factory.vertexCount();
        for (const auto& p : _geomCache.localPoly)
            factory.addVertex(p[0], p[1], fillColor);
        for (auto idx : _geomCache.earIndices)
            factory.mesh.indices.push_back(firstPolyIdx + idx);
    }

    // Stroke rendered on top of fill, extruded inward so it stays within the boundary.
    // addQuadraticStrokePath samples internally and uses M — not cached.
    BP_T(t4);
    if (hasStroke) {
        factory.addQuadraticStrokePath(
            _geomCache.curves, _geomCache.strokeWidth, strokeColor, _closed, _closed);
    }
    BP_T(t5);

    if (BP_US(t0, t5) > 400)
        VC_LOG(std::format(
            "[bezier] buildPath:{}µs  geom:{}µs  factory:{}µs  fill:{}µs  stroke:{}µs  pts:{}\n",
            BP_US(t0, t1), BP_US(t1, t2), BP_US(t2, t3), BP_US(t3, t4), BP_US(t4, t5), n));

    return factory.generateMesh();
}
