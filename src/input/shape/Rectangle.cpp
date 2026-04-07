/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Rectangle
*/

#include "input/shape/Rectangle.hpp"

#include <algorithm>

#include "vulkan/MeshFactory.hpp"

Rectangle::Rectangle(json::object_t &&args)
    : AInput(std::move(args))
{
}

Mesh Rectangle::getMesh(const Metadata &meta, const Config &config)
{
    float rawW          = meta.args.at("width").get<float>();
    float rawH          = meta.args.at("height").get<float>();
    float strokeWidth   = meta.args.at("strokeWidth").get<float>();
    float cornerRadiusPct = meta.args.at("cornerRadius").get<float>();

    // cornerRadius is a percentage of half the shorter side, clamped so the
    // shape never degenerates (r ≤ min half-extent).
    float maxR        = std::min(rawW, rawH) / 2.f;
    float cornerRadius = (cornerRadiusPct / 100.f) * maxR;

    cv::Vec4b fillColor   = colorFromJson(meta.args.at("fillColor"),   meta.opacity);
    cv::Vec4b strokeColor = colorFromJson(meta.args.at("strokeColor"), meta.opacity);

    float hw = rawW / 2.f;
    float hh = rawH / 2.f;
    float cx = hw;
    float cy = hh;

    MeshFactory factory({rawW, rawH}, meta, config);
    factory.addSdfShape(cx, cy, hw, hh, cornerRadius, strokeWidth / 2.f, fillColor, strokeColor);
    return factory.generateMesh();
}
