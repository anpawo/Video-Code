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

class Circle final : public ABCConcreteInput
{
public:

    Circle(const json::object_t &args, int framerate);
    ~Circle() = default;

private:

    const std::string _text;
};
