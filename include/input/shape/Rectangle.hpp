/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Rectangle
*/

#pragma once

#include <nlohmann/json.hpp>

#include "input/AInput.hpp"
#include "vulkan/Mesh.hpp"

using json = nlohmann::json;

class Rectangle final : public AInput
{
public:

    explicit Rectangle(json::object_t &&args);
    ~Rectangle() = default;

    Mesh getMesh(const Metadata &meta, const Config &config);
};
