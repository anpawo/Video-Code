/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Circle
*/

#pragma once

#include <nlohmann/json.hpp>

#include "input/AInput.hpp"
#include "vulkan/Mesh.hpp"

using json = nlohmann::json;

class Circle final : public AInput
{
public:

    Circle(json::object_t &&args);
    ~Circle() = default;

    Mesh getMesh(const Metadata &meta, const Config &config);
};
