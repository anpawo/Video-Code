/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Circle
*/

#include "input/shape/Circle.hpp"

#include <cmath>

#include "vulkan/MeshFactory.hpp"

// 8 arcs (45° each) give a mathematically exact circle boundary.
// The geometry shader tessellates each arc adaptively.
static constexpr int   BEZIER_SEGS = 8;
static constexpr float PI          = static_cast<float>(M_PI);

Circle::Circle(json::object_t &&args)
    : AInput(std::move(args))
{
}

Mesh Circle::getMesh(const Metadata &meta, const Config &config)
{
    float radius      = meta.args.at("radius").get<float>();
    float strokeWidth = meta.args.at("strokeWidth").get<float>();

    cv::Vec4b fillColor   = colorFromJson(meta.args.at("fillColor"),   meta.opacity);
    cv::Vec4b strokeColor = colorFromJson(meta.args.at("strokeColor"), meta.opacity);

    float       diameter = radius * 2.f;
    float       cx = radius, cy = radius; // center in local space
    MeshFactory factory({diameter, diameter}, meta, config);

    // ── Fill: N Bézier arc segments ────────────────────────────────────────
    // Each segment contributes:
    //   1. A center-fan triangle (solid fill, UV sentinel) covering the chord.
    //   2. A Bézier cap triangle (Loop-Blinn UV) covering the arc hump.
    // Together they tile the full disc with mathematically correct curved edges.
    if (fillColor[3] > 0) {
        for (int i = 0; i < BEZIER_SEGS; i++) {
            float t0    = 2.f * PI * i       / BEZIER_SEGS;
            float t1    = 2.f * PI * (i + 1) / BEZIER_SEGS;
            float tmid  = (t0 + t1) * 0.5f;
            float dthalf = (t1 - t0) * 0.5f; // half the arc angle

            // Arc endpoints on the circle
            float p0x = cx + radius * std::cos(t0);
            float p0y = cy + radius * std::sin(t0);
            float p2x = cx + radius * std::cos(t1);
            float p2y = cy + radius * std::sin(t1);

            // Control point: tangent-line intersection, sits outside the circle.
            // Formula: r / cos(half-arc-angle) in the midpoint direction.
            float factor = 1.f / std::cos(dthalf);
            float p1x = cx + radius * factor * std::cos(tmid);
            float p1y = cy + radius * factor * std::sin(tmid);

            // Center-fan triangle: covers the chord (straight edge).
            uint16_t base = factory.vertexCount();
            factory.addVertex(cx,  cy,  fillColor);
            factory.addVertex(p0x, p0y, fillColor);
            factory.addVertex(p2x, p2y, fillColor);
            factory.addIndex(base);
            factory.addIndex(base + 1);
            factory.addIndex(base + 2);

            // Bézier cap: smooths the boundary between chord and actual arc.
            factory.addBezierCap(p0x, p0y, p1x, p1y, p2x, p2y, fillColor);
        }
    }

    // ── Stroke: 8 quadratic Bézier arc primitives ─────────────────────────
    // Each arc uses the same control points as the fill caps.
    // The geometry shader tessellates them into smooth anti-aliased strips.
    if (strokeColor[3] > 0 && strokeWidth > 0.f) {
        for (int i = 0; i < BEZIER_SEGS; i++) {
            float t0    = 2.f * PI * i       / BEZIER_SEGS;
            float t1    = 2.f * PI * (i + 1) / BEZIER_SEGS;
            float tmid  = (t0 + t1) * 0.5f;
            float dthalf = (t1 - t0) * 0.5f;

            float p0x = cx + radius * std::cos(t0);
            float p0y = cy + radius * std::sin(t0);
            float p2x = cx + radius * std::cos(t1);
            float p2y = cy + radius * std::sin(t1);

            float factor = 1.f / std::cos(dthalf);
            float p1x = cx + radius * factor * std::cos(tmid);
            float p1y = cy + radius * factor * std::sin(tmid);

            factory.addBezierStroke(p0x, p0y, p1x, p1y, p2x, p2y, strokeWidth, strokeColor);
        }
    }

    return factory.generateMesh();
}
