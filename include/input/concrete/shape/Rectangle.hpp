/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Text
*/

#pragma once

#include <nlohmann/json.hpp>
#include <string>

#include "input/concrete/ABCConcreteInput.hpp"

using json = nlohmann::json;

class Rectangle final : public ABCConcreteInput
{
public:

    Rectangle(json::object_t &&args);
    ~Rectangle() = default;

private:

    const std::string _text;
};
