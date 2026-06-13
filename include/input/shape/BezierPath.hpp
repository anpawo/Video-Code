/*
** EPITECH PROJECT, 2026
** video-code
** File description:
** BezierPath
*/

#pragma once

#include <cstddef>
#include <limits>
#include <opencv2/core/matx.hpp>
#include <string>
#include <vector>

#include "input/AInput.hpp"
#include "utils/Color.hpp"         // GradientStop
#include "vulkan/MeshFactory.hpp"  // QuadraticBezier2D

// Base class for all vector shapes (like Manim's VMobject).
// Subclasses define their geometry as a path of quadratic bezier control points
// in anchor-handle format: [ a0, h0, a1, h1, a2, h2, ... ]
// Each triplet (a_i, h_i, a_{i+1 % n}) is one quadratic bezier segment.
// getMesh() tessellates the path into fill and stroke triangles.

class BezierPath : public AInput
{
public:

    BezierPath(json::object_t&& args);
    ~BezierPath() override = default;

    Mesh getMesh(const Metadata& meta, const Config& config) override;

protected:

    virtual void buildPath(const Metadata& meta) = 0;

    enum class GradType { None, Linear, Radial, Conic };

    // Reads `args[key]` — either a solid `[r,g,b,a]` (rgba), a linear gradient
    // `[stops, angle_number]`, a radial gradient `[stops, "radial"]`, or a conic
    // gradient `[stops, ["conic", angle_number]]` — into color/stops/gradType/angle.
    // When solid, `color` is set and `stops` is left empty.
    static void parseColorOrGradient(
        const json::object_t& args, const std::string& key,
        cv::Vec4b& color, std::vector<GradientStop>& stops, GradType& gradType, float& angle);

    std::vector<cv::Vec2f> _points; // anchor-handle-anchor-handle ...

    // Point count per contour, partitioning _points. Empty = one contour.
    // Multi-contour shapes (letter glyphs) are filled as outer/holes groups
    // (earcut with holes) and stroked one contour at a time.
    std::vector<size_t> _contourSizes;

    bool      _closed      = true;
    float     _strokeWidth = 0.f;
    cv::Vec4b _fillColor   = {0, 0, 0, 0};
    cv::Vec4b _strokeColor = {0, 0, 0, 255};
    std::vector<GradientStop> _fillStops;
    std::vector<GradientStop> _strokeStops;
    GradType  _fillGradType   = GradType::None;
    GradType  _strokeGradType = GradType::None;
    float     _fillGradientAngle   = 0.f; // degrees — 0 = left→right, 90 = bottom→top (linear & conic)
    float     _strokeGradientAngle = 0.f;

private:

    // Per-shape geometry cache.
    // Stores the expensive-to-compute local-space results (bezier sample + earcut).
    // Keyed on a FNV-1a hash of _points + scale + rotation.
    // Invalidated when the shape geometry or display scale changes.
    // One outer ring + its hole rings — mirrors the earcut-with-holes grouping,
    // kept separate (rather than just concatenated in localPoly) so multi-stop
    // linear fills can re-clip+re-earcut each group per gradient band.
    struct FillGroup {
        std::vector<cv::Vec2f>              outer;
        std::vector<std::vector<cv::Vec2f>> holes;
    };

    struct GeomCache {
        std::vector<cv::Vec2f>         localPoly;  // sampled fill vertices (outer/holes groups concatenated)
        std::vector<uint32_t>          earIndices; // earcut of localPoly (used for solid fills and 2-stop gradients)
        std::vector<QuadraticBezier2D> curves;     // offset-adjusted bezier segments (all contours)
        cv::Size2f                     localSize;  // bounding box dimensions

        // (first curve, curve count) per contour — strokes run one contour at a time.
        std::vector<std::pair<size_t, size_t>> contourCurves;

        // Largest outer ring of sampled points — boundary for radial/conic fills.
        std::vector<cv::Vec2f> boundaryRing;

        // Outer+holes groups — used by multi-stop linear fills to respect holes.
        std::vector<FillGroup> fillGroups;
    };

    size_t    _lastGeomHash{std::numeric_limits<size_t>::max()};
    bool      _geomValid{false};
    GeomCache _geomCache;

    // --- Mesh-level cache (position/opacity-only animation) --------------------
    // MeshFactory still re-emits every vertex (stroke extrusion, fill assembly,
    // M-transform → NDC) on every call, even when the geometry cache above is
    // valid. When only meta.position or meta.opacity changed since the last
    // build, the resulting Mesh differs from the cached one by a uniform NDC
    // translation and a uniform alpha scale — apply that directly and skip
    // MeshFactory entirely. Keyed on a hash extending the geometry hash with the
    // remaining fields that affect vertex colors/positions (fill/stroke colors,
    // gradients, align).
    size_t     _lastMeshHash{std::numeric_limits<size_t>::max()};
    bool       _meshCacheValid{false};
    Mesh       _meshCache;
    cv::Vec2f  _meshCachePosition{0.f, 0.f};
    uint8_t    _meshCacheOpacity{0};
    cv::Size2f _meshCacheScreen{0.f, 0.f};
};
