/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** IFragmentShader
*/

#pragma once

#include <nlohmann/json.hpp>
#include <string_view>
#include <vector>

using json = nlohmann::json;

struct IFragmentShader
{
    virtual ~IFragmentShader() = default;

    virtual size_t start() const = 0;

    // The class name used to find the GLSL file: "Blur" → assets/shaders/blur/frag.glsl
    virtual std::string_view shaderName() const = 0;

    virtual const json::object_t& args() const = 0;

    // Ordered floats from args (excluding start/duration). Passed as pc.p[] to the GLSL shader.
    std::vector<float> shaderParams() const
    {
        std::vector<float> out;
        for (const auto& [k, v] : args()) {
            if (k != "start" && k != "duration" && v.is_number())
                out.push_back(v.get<float>());
        }
        return out;
    }

    // Math-shader params: the origin FIRST, at fixed slots, then everything
    // else alphabetically. A math shader draws around a point rather than
    // across the frame, so every one of them reads that point at the same
    // p[] index whatever its own args happen to be called — the alphabetical
    // rule would otherwise put it somewhere different in each file.
    //
    // Shared by the two ways a math shader reaches the renderers: as a
    // timeline effect (MathShader::paramsAtFrame) and as a fill paint, which
    // is built straight from the json and never sees the ShaderFactory
    // (AInput::getActiveEffectsAtFrame).
    static void pushMathParams(const json::object_t& args, std::vector<float>& out)
    {
        auto arg = [&](const char* key, float fallback) {
            auto it = args.find(key);
            return it != args.end() && it->second.is_number() ? it->second.get<float>() : fallback;
        };
        out.push_back(arg("originX", 50.f));       // percent of the host box, or pixels
        out.push_back(arg("originY", 50.f));       // 50/50 = its centre
        out.push_back(arg("originUnit", 0.f));     // 0 = percent, 1 = pixels

        for (const auto& [k, v] : args) {
            if (k != "start" && k != "duration" && k != "originX" && k != "originY" && k != "originUnit" && v.is_number())
                out.push_back(v.get<float>());
        }
    }

    // Params for a specific frame. Most effects are constant over their
    // duration; time-driven ones (e.g. LightSweep) override this to append
    // per-frame values such as the animation progress.
    virtual std::vector<float> paramsAtFrame(size_t /*frame*/) const { return shaderParams(); }

    // Geometry-dependent param resolution — consumed by resolveEffectParams()
    // (vulkan/EffectResolver.hpp), the single shared pass both renderers run.
    // Shaders whose GLSL needs to know where the object is on screen declare
    // it here instead of being name-matched inside the renderers.

    // The mesh's own screen-space bounding box (uMin, vMin, uMax, vMax) is
    // PREPENDED to the params; the GLSL reads it as p[0..3] and does its own
    // object-relative math (e.g. Crop percentages, Vignette falloff).
    virtual bool needsBBox() const { return false; }

    // >= 0 marks params[groupParamIndex()] as a group id: every mesh whose
    // effect shares the id gets the UNION of their bounding boxes prepended
    // (and the id itself removed). Needed by effects that must animate
    // continuously across several meshes as one area (e.g. LightSweep over a
    // Text's letters) — a plain needsBBox can't express it because the union
    // isn't known until every mesh of the frame has been seen.
    virtual int groupParamIndex() const { return -1; }
};
