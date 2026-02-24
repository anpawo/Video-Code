/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Input
*/

#pragma once

#include <functional>
#include <memory>
#include <nlohmann/json.hpp>
#include <opencv2/core/mat.hpp>
#include <string>

#include "shader/IFragmentShader.hpp"

using json = nlohmann::json;

class IInput
{
public:

    using ShaderFactoryCallback = std::unique_ptr<IFragmentShader> (*)(void* context, const std::string& name, const json::object_t& args);

    IInput() = default;
    virtual ~IInput() = default;

    // -

    virtual cv::Mat getBaseMatrix(const json::object_t& args) = 0;

    // -

    virtual void add(nlohmann::basic_json<>& modification) = 0;

    // -

    virtual void overlay(cv::Mat& bg, size_t t) = 0;

    // -

    virtual void setShaderFactory(void* context, ShaderFactoryCallback callback) = 0;

    // -

    virtual size_t maxFrameHint() const { return 0; }

    // -
};
