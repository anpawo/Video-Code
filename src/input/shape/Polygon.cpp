/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Polygon
*/

#include "input/shape/Polygon.hpp"

#include <algorithm>

Polygon::Polygon(json::object_t&& args)
    : BezierPath(std::move(args))
{
}

void Polygon::buildPath(const json::object_t& args)
{
    auto raw = args.at("points").get<std::vector<std::vector<float>>>();
    _strokeWidth = args.at("strokeWidth").get<float>() * config::worldToPixelRatio;
    _fillColor   = colorFromJson(args.at("fillColor"),  255);
    _strokeColor = colorFromJson(args.at("strokeColor"), 255);
    _closed      = true;

    int n = static_cast<int>(raw.size());
    if (n < 2)
        return;

    std::vector<cv::Vec2f> pts(n);
    for (int i = 0; i < n; ++i)
        pts[i] = {raw[i][0] * config::worldToPixelRatio, raw[i][1] * config::worldToPixelRatio};

    float rFrac = 0.f;
    if (args.count("cornerRadius"))
        rFrac = std::clamp(args.at("cornerRadius").get<float>(), 0.f, 100.f) / 100.f;

    auto unitVec = [](cv::Vec2f v) -> cv::Vec2f {
        float len = std::hypot(v[0], v[1]);
        return len > 1e-6f ? v * (1.f / len) : cv::Vec2f{0.f, 0.f};
    };

    auto edgeLen = [&](int i, int j) {
        return std::hypot(pts[j][0] - pts[i][0], pts[j][1] - pts[i][1]);
    };

    if (rFrac <= 0.f) {
        // Straight polygon: each edge is one quadratic bezier segment (handle = midpoint).
        for (int i = 0; i < n; ++i) {
            cv::Vec2f a = pts[i];
            cv::Vec2f b = pts[(i + 1) % n];
            _points.push_back(a);
            _points.push_back((a + b) * 0.5f);
        }
        return;
    }

    // Rounded corners: each corner becomes a quadratic arc (control point = corner vertex),
    // joined by midpoint-handle straight segments.
    // Layout (4 points per vertex, 2 segments per vertex):
    //   arcStart(i), pts[i], arcEnd(i), mid(arcEnd(i), arcStart(i+1))
    std::vector<cv::Vec2f> arcStart(n), arcEnd(n);
    for (int i = 0; i < n; ++i) {
        int   prev = (i - 1 + n) % n;
        int   next = (i + 1) % n;
        float maxR = std::min(edgeLen(prev, i), edgeLen(i, next)) * 0.5f;
        float r    = rFrac * maxR;
        arcStart[i] = pts[i] + unitVec(pts[prev] - pts[i]) * r;
        arcEnd[i]   = pts[i] + unitVec(pts[next] - pts[i]) * r;
    }

    for (int i = 0; i < n; ++i) {
        int nextI = (i + 1) % n;
        _points.push_back(arcStart[i]);
        _points.push_back(pts[i]);
        _points.push_back(arcEnd[i]);
        _points.push_back((arcEnd[i] + arcStart[nextI]) * 0.5f);
    }
}
