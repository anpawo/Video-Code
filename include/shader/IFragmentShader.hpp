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
};
