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

class Rectangle final : public AInput
{
public:

    Rectangle(json::object_t &&args);
    ~Rectangle() = default;

    void construct() final;
};
