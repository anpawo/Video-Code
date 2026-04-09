/*
** EPITECH PROJECT, 2026
** video-code
** File description:
** BezierPath
*/

#pragma once

#include <opencv2/core/matx.hpp>
#include <vector>

#include "input/AInput.hpp"

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

    std::vector<cv::Vec2f> _points; // anchor-handle-anchor-handle ...
    bool      _closed      = true;
    float     _strokeWidth = 0.f;
    cv::Vec4b _fillColor   = {0, 0, 0, 0};
    cv::Vec4b _strokeColor = {0, 0, 0, 255};
};
