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

class Circle final : public AInput
{
public:

    Circle(json::object_t &&args);
    ~Circle() = default;

    void construct() final;
};
