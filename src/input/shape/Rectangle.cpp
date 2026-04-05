/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Rectangle
*/

#include "input/shape/Rectangle.hpp"

#include <algorithm>

#include "geometry/Arc.hpp"
#include "vulkan/MeshFactory.hpp"

static constexpr int   ARC_SEGMENTS = 16;
static constexpr float PI = static_cast<float>(M_PI);

// Returns the outline of a rounded rectangle as a flat list of points going
// clockwise. Each corner is an arc of ARC_SEGMENTS segments.
// When cornerRadius == 0 each arc degenerates to a single corner point.
static std::vector<cv::Vec2f> roundedRectOutline(float w, float h, float r, int n)
{
    std::vector<cv::Vec2f> pts;

    auto addCorner = [&](float cx, float cy, float startAngle, float endAngle) {
        if (r > 0.f) {
            auto arc = arcPoints(cx, cy, r, startAngle, endAngle, n);
            pts.insert(pts.end(), arc.begin(), arc.end());
        } else {
            for (int i = 0; i <= n; i++) {
                pts.push_back({cx, cy});
            }
        }
    };

    addCorner(w - r, r, -PI / 2.f, 0.f);    // top-right
    addCorner(w - r, h - r, 0.f, PI / 2.f); // bottom-right
    addCorner(r, h - r, PI / 2.f, PI);      // bottom-left
    addCorner(r, r, PI, 3.f * PI / 2.f);    // top-left

    return pts;
}

Rectangle::Rectangle(json::object_t &&args)
    : AInput(std::move(args))
{
}

Mesh Rectangle::getMesh(const Metadata &meta, const Config &config)
{
    float rawW = meta.args.at("width").get<float>();
    float rawH = meta.args.at("height").get<float>();
    float strokeWidth      = meta.args.at("strokeWidth").get<float>();
    float cornerRadiusPct  = meta.args.at("cornerRadius").get<float>();
    float cornerRadius     = (cornerRadiusPct / 100.f) * std::min(rawW, rawH) / 2.f;

    cv::Vec4b fillColor = colorFromJson(meta.args.at("fillColor"), meta.opacity);
    cv::Vec4b strokeColor = colorFromJson(meta.args.at("strokeColor"), meta.opacity);

    MeshFactory factory({rawW, rawH}, meta, config);

    auto outerPts = roundedRectOutline(rawW, rawH, cornerRadius, ARC_SEGMENTS);
    auto n = static_cast<uint16_t>(outerPts.size());

    // Inner outline — stroke lives between outer and inner, fully inside
    float innerR = std::max(cornerRadius - strokeWidth, 0.f);
    float innerW = rawW - 2.f * strokeWidth;
    float innerH = rawH - 2.f * strokeWidth;
    auto  innerPts = roundedRectOutline(innerW, innerH, innerR, ARC_SEGMENTS);
    for (auto &p : innerPts) {
        p[0] += strokeWidth;
        p[1] += strokeWidth;
    }

    // --- Fill: triangle fan from center to outer outline ---
    if (fillColor[3] > 0) {
        uint16_t base = factory.vertexCount();
        uint16_t center = base;
        factory.addVertex(rawW / 2.f, rawH / 2.f, fillColor);
        for (const auto &p : outerPts) {
            factory.addVertex(p[0], p[1], fillColor);
        }

        for (uint16_t i = 0; i < n; i++) {
            factory.addIndex(center);
            factory.addIndex(base + 1 + i);
            factory.addIndex(base + 1 + (i + 1) % n);
        }
    }

    // --- Stroke: ring from outer to inner outline, drawn on top ---
    if (strokeColor[3] > 0 && strokeWidth > 0.f) {
        uint16_t base = factory.vertexCount();
        for (const auto &p : outerPts) {
            factory.addVertex(p[0], p[1], strokeColor);
        }

        for (const auto &p : innerPts) {
            factory.addVertex(p[0], p[1], strokeColor);
        }

        for (uint16_t i = 0; i < n; i++) {
            uint16_t j = (i + 1) % n;
            uint16_t o0 = base + i, o1 = base + j;
            uint16_t i0 = base + n + i, i1 = base + n + j;
            factory.addIndex(o0);
            factory.addIndex(o1);
            factory.addIndex(i0);
            factory.addIndex(o1);
            factory.addIndex(i1);
            factory.addIndex(i0);
        }
    }

    return factory.generateMesh();
}
