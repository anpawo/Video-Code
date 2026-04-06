/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Text
*/

#pragma once

#include <nlohmann/json.hpp>

#include "input/AInput.hpp"
#include "input/text/GlyphCache.hpp"
#include "vulkan/Mesh.hpp"

using json = nlohmann::json;

class Text final : public AInput
{
public:

    Text(json::object_t &&args);
    ~Text() = default;

    Mesh getMesh(const Metadata &meta, const Config &config);

private:

    static GlyphCache &glyphCache();
};
