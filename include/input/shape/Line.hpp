/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Text
*/

#pragma once

#include <nlohmann/json.hpp>

#include "input/AInput.hpp"

using json = nlohmann::json;

class Line final : public AInput
{
public:

    Line(json::object_t &&args);
    ~Line() = default;

    cv::Mat getBaseMatrix(const json::object_t &args);
};
