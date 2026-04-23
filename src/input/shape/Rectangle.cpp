/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Rectangle
*/

#include "input/shape/Rectangle.hpp"

#include <algorithm>

Rectangle::Rectangle(json::object_t&& args)
    : BezierPath(std::move(args))
{
}

// A rectangle with optional rounded corners built from quadratic bezier segments.
// Straight edges use a midpoint handle; rounded corners use a single quadratic arc
// whose handle is the corner vertex (this approximates a 90° circular arc well).
void Rectangle::buildPath(const json::object_t& args)
{
    float w = args.at("width").get<float>();
    float h = args.at("height").get<float>();
    _strokeWidth = args.at("strokeWidth").get<float>();
    _fillColor = colorFromJson(args.at("fillColor"), 255);
    _strokeColor = colorFromJson(args.at("strokeColor"), 255);
    _closed = true;

    float r = 0.f;
    if (args.count("cornerRadius"))
        r = args.at("cornerRadius").get<float>() / 100.f * std::min(w, h) * 0.5f;
    r = std::min(r, std::min(w, h) * 0.5f);

    float hw = w / 2.f;
    float hh = h / 2.f;
    if (r <= 0.f) {
        // Plain rectangle: 4 straight segments (handle = midpoint).
        cv::Vec2f tl{-hw, -hh}, tr{hw, -hh};
        cv::Vec2f br{hw, hh}, bl{-hw, hh};
        auto      mid = [](cv::Vec2f a, cv::Vec2f b) { return (a + b) * 0.5f; };
        _points = {
            tl,
            mid(tl, tr),
            tr,
            mid(tr, br),
            br,
            mid(br, bl),
            bl,
            mid(bl, tl),
        };
        return;
    }

    // Rounded rectangle: 12 segments (4 straight edges + 4×2 corner arc segments).
    // Each 90° corner uses 2 quadratic bezier segments of 45° — same as Manim's
    // RoundedRectangle with n_components=2.
    //
    // The path must use the same winding as the plain rectangle (top -> right ->
    // bottom -> left in screen coordinates) so the shared "inside stroke" code
    // keeps the stroke and fill inset toward the rectangle interior.
    const float dTheta = static_cast<float>(M_PI) / 2.f; // 90° turn per corner
    const float cosHalf = std::cos(dTheta / 4.f);        // cos(22.5°) ≈ 0.9239

    // Push 4 points (2 segments) for a corner arc. The implied endpoint a2
    // must match the first anchor of the next segment (straight or arc).
    auto cornerArc = [&](float alpha, cv::Vec2f C) {
        for (int i = 0; i < 2; ++i) {
            float aAngle = alpha + i * (dTheta / 2.f);
            float hAngle = alpha + (i + 0.5f) * (dTheta / 2.f);
            _points.push_back(C + r * cv::Vec2f{std::cos(aAngle), std::sin(aAngle)});
            _points.push_back(C + (r / cosHalf) * cv::Vec2f{std::cos(hAngle), std::sin(hAngle)});
        }
    };

    auto straight = [&](cv::Vec2f a, cv::Vec2f b) {
        _points.push_back(a);
        _points.push_back((a + b) * 0.5f);
    };

    // Arc centers for each rounded corner (offset inward by r).
    // Match the plain rectangle winding: TL -> TR -> BR -> BL.
    straight({-hw + r, -hh}, {hw - r, -hh});                       // top edge
    cornerArc(-static_cast<float>(M_PI) / 2.f, {hw - r, -hh + r}); // top-right
    straight({hw, -hh + r}, {hw, hh - r});                         // right edge
    cornerArc(0.f, {hw - r, hh - r});                              // bottom-right
    straight({hw - r, hh}, {-hw + r, hh});                         // bottom edge
    cornerArc(static_cast<float>(M_PI) / 2.f, {-hw + r, hh - r});  // bottom-left
    straight({-hw, hh - r}, {-hw, -hh + r});                       // left edge
    cornerArc(static_cast<float>(M_PI), {-hw + r, -hh + r});       // top-left
}
