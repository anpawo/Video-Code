/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Register
*/

#pragma once

#include <algorithm>
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
    X(Contrast)    \
    X(Sharpen)     \
    X(Crop)

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
// Time-driven shaders (declared by hand: they override paramsAtFrame)
// -------------------------------------------------------------------------

// LightSweep — a bright band sweeping across the input over the effect's
// duration. shaderParams() yields [angle, intensity, width] (alphabetical);
// paramsAtFrame appends the 0..1 progress so the GLSL side only interpolates.
class LightSweep final : public IFragmentShader
{
public:

    LightSweep(const json::object_t& args)
        : _start(args.at("start").get<size_t>())
        , _duration(args.at("duration").get<size_t>())
        , _args(args)
    {
    }

    size_t start() const override { return _start; }

    std::string_view shaderName() const override { return "LightSweep"; }

    const json::object_t& args() const override { return _args; }

    std::vector<float> paramsAtFrame(size_t frame) const override
    {
        std::vector<float> out = shaderParams();
        // Single-frame application: show the band mid-sweep instead of off-object.
        float progress = _duration <= 1
                             ? 0.5f
                             : static_cast<float>(frame - _start) / static_cast<float>(_duration - 1);
        out.push_back(std::clamp(progress, 0.f, 1.f));
        return out;
    }

private:

    const size_t         _start;
    const size_t         _duration;
    const json::object_t _args;
};

// -------------------------------------------------------------------------
// Factory map: shader name → constructor
// -------------------------------------------------------------------------

#define BIND_SHADERS(name) \
    {#name, [](const json::object_t& args) -> std::unique_ptr<IFragmentShader> { return std::make_unique<name>(args); }},

const std::map<std::string, std::function<std::unique_ptr<IFragmentShader>(const json::object_t&)>> transformation{
    SHADERS(BIND_SHADERS)
        BIND_SHADERS(LightSweep)
};
