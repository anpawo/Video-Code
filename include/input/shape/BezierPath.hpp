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

    virtual void buildPath(const json::object_t& args) = 0;

    enum class GradType { None, Linear, Radial, Conic };

    // Reads `args[key]` — either a solid `[r,g,b,a]` (rgba), a linear gradient
    // `[stops, angle_number]`, a radial gradient `[stops, "radial"]`, or a conic
    // gradient `[stops, ["conic", angle_number]]` — into color/stops/gradType/angle.
    // When solid, `color` is set and `stops` is left empty.
    static void parseColorOrGradient(
        const json::object_t& args, const std::string& key,
        cv::Vec4b& color, std::vector<GradientStop>& stops, GradType& gradType, float& angle);

    std::vector<cv::Vec2f> _points; // anchor-handle-anchor-handle ...
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
    struct GeomCache {
        std::vector<cv::Vec2f>         localPoly;  // sampled bezier polygon
        std::vector<uint16_t>          earIndices; // earcut of localPoly (used for solid fills and 2-stop gradients)
        std::vector<QuadraticBezier2D> curves;     // offset-adjusted bezier segments
        cv::Size2f                     localSize;  // bounding box dimensions
    };

    size_t    _lastGeomHash{std::numeric_limits<size_t>::max()};
    bool      _geomValid{false};
    GeomCache _geomCache;
};
