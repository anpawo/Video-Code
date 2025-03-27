/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Group
*/

#pragma once

#include <nlohmann/json.hpp>

#include "input/concrete/ABCConcreteInput.hpp"

using json = nlohmann::json;

class Group final : public ABCConcreteInput
{
public:

    Group(const std::vector<std::shared_ptr<IInput>>& inputs, const json::object_t& args);
    ~Group() = default;
};
