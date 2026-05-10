/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Input
*/

#pragma once

#include <nlohmann/json.hpp>

#include "core/Config.hpp"
#include "input/Metadata.hpp"
#include "vulkan/Mesh.hpp"

using json = nlohmann::json;

class IInput
{
public:

    IInput() = default;
    virtual ~IInput() = default;

    // -

    virtual Mesh getMesh(const Metadata& meta, const Config& config) = 0;

    // -

    virtual void add(nlohmann::basic_json<>& modification) = 0;

    // -

    virtual Metadata getMetadata(size_t index) = 0;
};
