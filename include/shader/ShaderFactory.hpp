/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Register
*/

#pragma once

#include <functional>
#include <map>
#include <nlohmann/json.hpp>
#include <string>

#include "shader/IFragmentShader.hpp"

using json = nlohmann::json;

// -----------------------------------------------------------------------------
// Registered fragment shaders
// -----------------------------------------------------------------------------

#define SHADERS(X) \
    X(Blur)        \
    X(Grayscale)   \
    X(Gamma)       \
    X(Grain)       \
    X(Brightness)  \
    X(Contrast)

// -------------------------------------------------------------------------
// Generated class for each registered shader
// -------------------------------------------------------------------------
#define DECLARE_SHADERS(name)                                               \
    class name final : public IFragmentShader                               \
    {                                                                       \
    public:                                                                 \
                                                                            \
        name(const json::object_t& args)                                    \
            : _start(args.at("start").get<size_t>())                        \
            , _duration(args.at("duration").get<size_t>())                  \
            , _args(args) {}                                                \
                                                                            \
        size_t                start() const override { return _start; }     \
        std::string_view      shaderName() const override { return #name; } \
        const json::object_t& args() const override { return _args; }       \
                                                                            \
    private:                                                                \
                                                                            \
        const size_t         _start;                                        \
        const size_t         _duration;                                     \
        const json::object_t _args;                                         \
    };

SHADERS(DECLARE_SHADERS)

// -------------------------------------------------------------------------
// Factory map: shader name → constructor
// -------------------------------------------------------------------------

#define BIND_SHADERS(name) \
    {#name, [](const json::object_t& args) -> std::unique_ptr<IFragmentShader> { return std::make_unique<name>(args); }},

const std::map<std::string, std::function<std::unique_ptr<IFragmentShader>(const json::object_t&)>> transformation{
    SHADERS(BIND_SHADERS)
};
