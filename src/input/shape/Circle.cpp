/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Circle
*/

#include "input/shape/Circle.hpp"

#include "vulkan/MeshFactory.hpp"

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

    float diameter = radius * 2.f;
    float cx = radius;
    float cy = radius;

    // A circle is sdRoundedBox with hw = hh = r = radius.
    MeshFactory factory({diameter, diameter}, meta, config);
    factory.addSdfShape(cx, cy, radius, radius, radius, strokeWidth / 2.f, fillColor, strokeColor);
    return factory.generateMesh();
}
