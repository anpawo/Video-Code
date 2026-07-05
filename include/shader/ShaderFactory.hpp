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

// Pure pixel functions — params pass through to the GLSL untouched.
#define SHADERS(X) \
    X(Blur)        \
    X(Grayscale)   \
    X(Gamma)       \
    X(Grain)       \
    X(Brightness)  \
    X(Contrast)    \
    X(Sharpen)     \
    X(Pixelate)    \
    X(Duotone)     \
    X(Sepia)       \
    X(Invert)      \
    X(Posterize)   \
    X(HueRotate)   \
    X(Halftone)

// Object-relative shaders — resolveEffectParams() prepends the mesh's own
// screen-space bounding box, so their GLSL reads p[0..3] = (uMin, vMin,
// uMax, vMax) followed by the regular alphabetical args.
#define BBOX_SHADERS(X) \
    X(Crop)             \
    X(Vignette)         \
    X(ZoomBlur)

// -------------------------------------------------------------------------
// Generated class for each registered shader
// -------------------------------------------------------------------------
#define DECLARE_SHADERS_COMMON(name)                                        \
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
        const json::object_t _args;

#define DECLARE_SHADERS(name)                 \
    class name final : public IFragmentShader \
    {                                         \
        DECLARE_SHADERS_COMMON(name)          \
    };

#define DECLARE_BBOX_SHADERS(name)                       \
    class name final : public IFragmentShader            \
    {                                                    \
    public:                                              \
                                                         \
        bool needsBBox() const override { return true; } \
                                                         \
        DECLARE_SHADERS_COMMON(name)                     \
    };

SHADERS(DECLARE_SHADERS)
BBOX_SHADERS(DECLARE_BBOX_SHADERS)

// -------------------------------------------------------------------------
// Time-driven shaders (declared by hand: they override paramsAtFrame)
// -------------------------------------------------------------------------

// LightSweep — a bright band sweeping across the input over the effect's
// duration. shaderParams() yields [angle, group, intensity, width]
// (alphabetical); paramsAtFrame appends the 0..1 progress so the GLSL side
// only interpolates. groupParamIndex() = 1 makes resolveEffectParams()
// replace the group id with the group's union bounding box (prepended).
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

    int groupParamIndex() const override { return 1; }

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

// Glitch — RGB split + random horizontal slice offsets. shaderParams() yields
// [amount, seed, slices] (alphabetical); paramsAtFrame appends the 0..1
// progress that drives the per-tick slice re-roll in the GLSL.
class Glitch final : public IFragmentShader
{
public:

    Glitch(const json::object_t& args)
        : _start(args.at("start").get<size_t>())
        , _duration(args.at("duration").get<size_t>())
        , _args(args)
    {
    }

    size_t start() const override { return _start; }

    std::string_view shaderName() const override { return "Glitch"; }

    const json::object_t& args() const override { return _args; }

    std::vector<float> paramsAtFrame(size_t frame) const override
    {
        std::vector<float> out = shaderParams();
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

// Vhs — scanlines + chroma shift + analog noise. Time-driven like Glitch:
// paramsAtFrame appends the 0..1 progress that re-rolls the noise/jitter.
class Vhs final : public IFragmentShader
{
public:

    Vhs(const json::object_t& args)
        : _start(args.at("start").get<size_t>())
        , _duration(args.at("duration").get<size_t>())
        , _args(args)
    {
    }

    size_t start() const override { return _start; }

    std::string_view shaderName() const override { return "Vhs"; }

    const json::object_t& args() const override { return _args; }

    std::vector<float> paramsAtFrame(size_t frame) const override
    {
        std::vector<float> out = shaderParams();
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
        BBOX_SHADERS(BIND_SHADERS)
            BIND_SHADERS(LightSweep)
                BIND_SHADERS(Glitch)
                    BIND_SHADERS(Vhs)
};
