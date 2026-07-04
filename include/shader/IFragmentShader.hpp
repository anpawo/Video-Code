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
