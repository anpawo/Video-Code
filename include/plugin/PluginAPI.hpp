/*
** EPITECH PROJECT, 2026
** video-code
** File description:
** Plugin API
*/

#pragma once

#include <memory>
#include <nlohmann/json.hpp>

#include "input/IInput.hpp"
#include "shader/IFragmentShader.hpp"

namespace VC
{
    using InputFactoryFunction = std::unique_ptr<IInput> (*)(nlohmann::json::object_t&& args);
    using FragmentShaderFactoryFunction = std::unique_ptr<IFragmentShader> (*)(const nlohmann::json::object_t& args);

    using RegisterInputFunction = void (*)(void* context, const char* name, InputFactoryFunction factory);
    using RegisterFragmentShaderFunction = void (*)(void* context, const char* name, FragmentShaderFactoryFunction factory);

    struct PluginRegistrar
    {
        void* context;
        RegisterInputFunction registerInput;
        RegisterFragmentShaderFunction registerFragmentShader;
    };
}

extern "C" {
using VCRegisterPluginFunction = void (*)(VC::PluginRegistrar* registrar);
}
