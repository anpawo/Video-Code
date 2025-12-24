/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Input
*/

#pragma once

#include <nlohmann/json.hpp>
#include <opencv2/core/mat.hpp>

using json = nlohmann::json;

class IInput
{
public:

    IInput() = default;
    virtual ~IInput() = default;

    // -

    virtual cv::Mat getBaseMatrix(const json::object_t& args) = 0;

    // -

    virtual void add(nlohmann::basic_json<>& modification) = 0;

    // -

    virtual void overlay(cv::Mat& bg, size_t t) = 0;

    // -
};
