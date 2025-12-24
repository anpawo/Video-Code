/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Register
*/

#pragma once

#include <map>
#include <nlohmann/json.hpp>
#include <string>

#include "transformation/IEffect.hpp"

using json = nlohmann::json;

// -----------------------------------------------------------------------------
// Transformations
// -----------------------------------------------------------------------------

#define TRANSFORMATIONS(X) \
    X(Grayscale)           \
    // X(Fade)

// -------------------------------------------------------------------------
// Function declaration
// -------------------------------------------------------------------------
#define DECLARE_TRANSFORMATION(name)  \
    class name final : public IEffect \
    {                                 \
    public:                           \
                                      \
        name(const json::object_t&);  \
                                      \
        void render(cv::Mat&, int);   \
    };

TRANSFORMATIONS(DECLARE_TRANSFORMATION)

// -------------------------------------------------------------------------
// Map binding
// -------------------------------------------------------------------------

#define BIND_TRANSFORMATION(name) \
    {#name, [](const json::object_t& args) -> std::unique_ptr<IEffect> { return std::make_unique<name>(args); }},

const std::map<std::string, std::function<std::unique_ptr<IEffect>(const json::object_t&)>> transformation{
    TRANSFORMATIONS(BIND_TRANSFORMATION)
};
