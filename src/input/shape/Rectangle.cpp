/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Text
*/

#include "input/shape/Rectangle.hpp"

#include <cstddef>
#include <vector>

#include "opencv2/core/matx.hpp"

Rectangle::Rectangle(json::object_t &&args)
    : AInput(std::move(args))
{
}

Vertex Rectangle::makeVertex(float x, float y, const cv::Vec4b &c)
{
    return Vertex{
        {x, y},
        {0.0f, 0.0f}, // UVs unused, zeroed (texture)
        {
            c[0] / 255.f,
            c[1] / 255.f,
            c[2] / 255.f,
            c[3] / 255.f
        }
    };
}

Mesh Rectangle::getMesh(const Metadata &meta, const Config &config)
{
    // Width - Height
    w = meta.args.at("width").get<float>() * meta.scale.x;
    h = meta.args.at("height").get<float>() * meta.scale.y;

    // X - Y
    x = meta.position.x - w * meta.align.x;
    y = meta.position.y - h * meta.align.y;

    // Vulkan NDC
    x = x / config.windowWidth - 1.f;
    y = y / config.windowHeight - 1.f;
    w /= config.windowWidth;
    h /= config.windowHeight;

    const auto &c = meta.args.at("color");
    colorRGBA = cv::Vec4b(c[0], c[1], c[2], c[3]);

    ///< TODO:
    thickness = meta.args.at("thickness");
    cornerRadius = meta.args.at("cornerRadius");
    filled = meta.args.at("filled");

    // 0---1
    // |  /|
    // | / |
    // |/  |
    // 2---3

    Mesh mesh;
    mesh.hasTexture = false;
    mesh.textureDescriptor = nullptr;

    mesh.vertices = {
        makeVertex(x, y, colorRGBA),         // 0 top-left
        makeVertex(x + w, y, colorRGBA),     // 1 top-right
        makeVertex(x, y + h, colorRGBA),     // 2 bottom-left
        makeVertex(x + w, y + h, colorRGBA), // 3 bottom-right
    };

    mesh.indices = {0, 1, 2, 1, 3, 2};

    mesh.pushConstants = RectPushConstants{
        w,
        h,
        thickness,
        cornerRadius,
        filled ? 1 : 0,
        0
    };

    return mesh;
}
