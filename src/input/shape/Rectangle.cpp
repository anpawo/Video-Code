/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Rectangle
*/

#include "input/shape/Rectangle.hpp"

#include <algorithm>
#include <cmath>

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
    float strokeWidth = meta.args.at("strokeWidth").get<float>();
    float cornerRadiusPct = meta.args.at("cornerRadius").get<float>();
    float cornerRadius = (cornerRadiusPct / 100.f) * std::min(rawW, rawH) / 2.f;

    cv::Vec4b fillColor = colorFromJson(meta.args.at("fillColor"), meta.opacity);
    cv::Vec4b strokeColor = colorFromJson(meta.args.at("strokeColor"), meta.opacity);

    MeshFactory factory({rawW, rawH}, meta, config);

    auto outerPts = roundedRectOutline(rawW, rawH, cornerRadius, ARC_SEGMENTS);
    auto n = static_cast<uint16_t>(outerPts.size());

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

        // Bézier caps for rounded corners — one cap per arc sub-segment.
        // Straight edges have no cap (control point == chord midpoint → zero area).
        // Each cap smooths the boundary between the polygon chord and the true arc.
        if (cornerRadius > 0.f) {
            struct Corner
            {
                float cx, cy, t0, t1;
            };

            Corner corners[4] = {
                {rawW - cornerRadius, cornerRadius, -PI / 2.f, 0.f},
                {rawW - cornerRadius, rawH - cornerRadius, 0.f, PI / 2.f},
                {cornerRadius, rawH - cornerRadius, PI / 2.f, PI},
                {cornerRadius, cornerRadius, PI, 3.f * PI / 2.f},
            };
            for (const auto &c : corners) {
                float dAngle = (c.t1 - c.t0) / ARC_SEGMENTS;
                float dthalf = dAngle * 0.5f;
                float factor = 1.f / std::cos(dthalf);
                for (int i = 0; i < ARC_SEGMENTS; i++) {
                    float t0 = c.t0 + i * dAngle;
                    float t1 = t0 + dAngle;
                    float tmid = (t0 + t1) * 0.5f;
                    float p0x = c.cx + cornerRadius * std::cos(t0);
                    float p0y = c.cy + cornerRadius * std::sin(t0);
                    float p2x = c.cx + cornerRadius * std::cos(t1);
                    float p2y = c.cy + cornerRadius * std::sin(t1);
                    float p1x = c.cx + cornerRadius * factor * std::cos(tmid);
                    float p1y = c.cy + cornerRadius * factor * std::sin(tmid);
                    factory.addBezierCap(p0x, p0y, p1x, p1y, p2x, p2y, fillColor);
                }
            }
        }
    }

    // --- Stroke: Bézier arcs for corners + degenerate Bézier for straight edges ---
    // Corner arcs use the same quadratic Bézier control points as the fill caps.
    // Straight edges are represented as degenerate quadratics (p1 = midpoint of p0p2).
    // The geometry shader tessellates everything into smooth anti-aliased strips.
    if (strokeColor[3] > 0 && strokeWidth > 0.f) {
        struct Corner { float cx, cy, t0, t1; };
        Corner corners[4] = {
            {rawW - cornerRadius, cornerRadius,        -PI / 2.f, 0.f        },
            {rawW - cornerRadius, rawH - cornerRadius,  0.f,       PI / 2.f  },
            {cornerRadius,        rawH - cornerRadius,  PI / 2.f,  PI        },
            {cornerRadius,        cornerRadius,          PI,        3.f*PI/2.f},
        };

        // Corner arcs (same Bézier arcs as the fill caps)
        if (cornerRadius > 0.f) {
            for (const auto &c : corners) {
                float dAngle = (c.t1 - c.t0) / ARC_SEGMENTS;
                float dthalf = dAngle * 0.5f;
                float factor = 1.f / std::cos(dthalf);
                for (int i = 0; i < ARC_SEGMENTS; i++) {
                    float t0   = c.t0 + i * dAngle;
                    float t1   = t0 + dAngle;
                    float tmid = (t0 + t1) * 0.5f;
                    float p0x  = c.cx + cornerRadius * std::cos(t0);
                    float p0y  = c.cy + cornerRadius * std::sin(t0);
                    float p2x  = c.cx + cornerRadius * std::cos(t1);
                    float p2y  = c.cy + cornerRadius * std::sin(t1);
                    float p1x  = c.cx + cornerRadius * factor * std::cos(tmid);
                    float p1y  = c.cy + cornerRadius * factor * std::sin(tmid);
                    factory.addBezierStroke(p0x, p0y, p1x, p1y, p2x, p2y, strokeWidth, strokeColor);
                }
            }
        }

        // Straight edges: top, right, bottom, left
        // Each is a degenerate quadratic (p1 = midpoint → straight line).
        float r = cornerRadius;
        struct Edge { float x0, y0, x2, y2; };
        Edge edges[4] = {
            {r,        0.f,       rawW - r,  0.f      }, // top
            {rawW,     r,         rawW,       rawH - r }, // right
            {rawW - r, rawH,      r,          rawH     }, // bottom
            {0.f,      rawH - r,  0.f,        r        }, // left
        };
        for (const auto &e : edges) {
            float mx = (e.x0 + e.x2) * 0.5f;
            float my = (e.y0 + e.y2) * 0.5f;
            factory.addBezierStroke(e.x0, e.y0, mx, my, e.x2, e.y2, strokeWidth, strokeColor);
        }
    }

    return factory.generateMesh();
}
