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

#include "shader/IFragmentShader.hpp"

using json = nlohmann::json;

// -----------------------------------------------------------------------------
// Transformations
// -----------------------------------------------------------------------------

#define SHADERS(X) \
    X(Grayscale)   \
    X(Opacity)     \
    X(Blur)        \
    X(GammaCorrection)

// -------------------------------------------------------------------------
// Function declaration
// -------------------------------------------------------------------------
#define DECLARE_SHADERS(name)                              \
    class name final : public IFragmentShader              \
    {                                                      \
    public:                                                \
                                                           \
        name(const json::object_t& args)                   \
            : _start(args.at("start").get<size_t>())       \
            , _duration(args.at("duration").get<size_t>()) \
            , _args(args) {};                              \
                                                           \
        void render(cv::Mat&, size_t) const;               \
                                                           \
        size_t start() const { return _start; }            \
                                                           \
    private:                                               \
                                                           \
        const size_t _start;                               \
        const size_t _duration;                            \
                                                           \
        const json::object_t _args;                        \
    };

SHADERS(DECLARE_SHADERS)

// -------------------------------------------------------------------------
// Map binding
// -------------------------------------------------------------------------

#define BIND_SHADERS(name) \
    {#name, [](const json::object_t& args) -> std::unique_ptr<IFragmentShader> { return std::make_unique<name>(args); }},

const std::map<std::string, std::function<std::unique_ptr<IFragmentShader>(const json::object_t&)>> transformation{
    SHADERS(BIND_SHADERS)
};
