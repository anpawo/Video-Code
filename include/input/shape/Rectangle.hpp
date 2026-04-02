/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Text
*/

#pragma once

#include <nlohmann/json.hpp>

#include "input/AInput.hpp"
#include "vulkan/Mesh.hpp"
#include "vulkan/Vertex.hpp"

using json = nlohmann::json;

struct RectPushConstants
{
    float sizeX, sizeY;
    float thickness;
    float cornerRadius;
    int   filled;
    int   hasTexture; // always 0 for Rectangle
};

class Rectangle final : public AInput
{
public:

    explicit Rectangle(json::object_t &&args);
    ~Rectangle() = default;

    Mesh getMesh(const Metadata &meta, const Config &config);

private:

    // Temporary Attributes
    float     x, y;
    float     w, h;
    float     thickness;
    cv::Vec4b colorRGBA;
    float     cornerRadius;
    bool      filled;

    Vertex makeVertex(float x, float y, const cv::Vec4b &c);
};
