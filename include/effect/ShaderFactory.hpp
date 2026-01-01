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

#include "effect/IShader.hpp"

using json = nlohmann::json;

// -----------------------------------------------------------------------------
// Transformations
// -----------------------------------------------------------------------------

#define SHADERS(X) \
    X(Grayscale)   \
    X(Opacity)     \
    X(Blur)

// -------------------------------------------------------------------------
// Function declaration
// -------------------------------------------------------------------------
#define DECLARE_SHADERS(name)                             \
    class name final : public IShader                     \
    {                                                     \
    public:                                               \
                                                          \
        name(const json::object_t& args)                  \
            : start(args.at("start").get<size_t>())       \
            , duration(args.at("duration").get<size_t>()) \
            , args(args) {};                              \
                                                          \
        void render(cv::Mat&, size_t) const;              \
                                                          \
        size_t offset() const { return start; }           \
                                                          \
    private:                                              \
                                                          \
        const size_t start;                               \
        const size_t duration;                            \
                                                          \
        const json::object_t args;                        \
    };

SHADERS(DECLARE_SHADERS)

// -------------------------------------------------------------------------
// Map binding
// -------------------------------------------------------------------------

#define BIND_SHADERS(name) \
    {#name, [](const json::object_t& args) -> std::unique_ptr<IShader> { return std::make_unique<name>(args); }},

const std::map<std::string, std::function<std::unique_ptr<IShader>(const json::object_t&)>> transformation{
    SHADERS(BIND_SHADERS)
};
