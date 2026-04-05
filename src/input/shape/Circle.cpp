/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Circle
*/

#include "input/shape/Circle.hpp"

#include <algorithm>

#include "geometry/Arc.hpp"
#include "vulkan/MeshFactory.hpp"

static constexpr int   CIRCLE_SEGMENTS = 64;
static constexpr float PI = static_cast<float>(M_PI);

Circle::Circle(json::object_t &&args)
    : AInput(std::move(args))
{
}

Mesh Circle::getMesh(const Metadata &meta, const Config &config)
{
    float radius = meta.args.at("radius").get<float>();
    float strokeWidth = meta.args.at("strokeWidth").get<float>();

    cv::Vec4b fillColor = colorFromJson(meta.args.at("fillColor"), meta.opacity);
    cv::Vec4b strokeColor = colorFromJson(meta.args.at("strokeColor"), meta.opacity);

    float       diameter = radius * 2.f;
    MeshFactory factory({diameter, diameter}, meta, config);

    // Full circle outline: CIRCLE_SEGMENTS points (pop the duplicate last point)
    auto outerPts = arcPoints(radius, radius, radius, 0.f, 2.f * PI, CIRCLE_SEGMENTS);
    outerPts.pop_back();
    auto n = static_cast<uint16_t>(outerPts.size());

    auto innerPts = arcPoints(radius, radius, std::max(radius - strokeWidth, 0.f), 0.f, 2.f * PI, CIRCLE_SEGMENTS);
    innerPts.pop_back();

    // --- Fill: triangle fan from center to outer outline ---
    if (fillColor[3] > 0) {
        uint16_t base = factory.vertexCount();
        uint16_t center = base;
        factory.addVertex(radius, radius, fillColor);
        for (const auto &p : outerPts) {
            factory.addVertex(p[0], p[1], fillColor);
        }

        for (uint16_t i = 0; i < n; i++) {
            factory.addIndex(center);
            factory.addIndex(base + 1 + i);
            factory.addIndex(base + 1 + (i + 1) % n);
        }
    }

    // --- Stroke: ring from outer to inner, drawn on top ---
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
