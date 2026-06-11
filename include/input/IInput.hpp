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

    ///< Record one timeline modification (a shader application). args is taken
    ///< by rvalue so the ~13k entries of an animated scene are moved, not copied.
    virtual void add(const std::string& name, const std::string& type, json::object_t&& args) = 0;

    // -

    virtual Metadata getMetadata(size_t index) = 0;
};
