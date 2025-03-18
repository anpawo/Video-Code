/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** color
*/

#pragma once

#include <nlohmann/json.hpp>

#include "vm/Register.hpp"

using json = nlohmann::json;

#define transformation(t) void t(std::shared_ptr<IInput> input, Register &reg, const json::object_t &args)

namespace transformation
{

    // Color
    /***
        TODO: transformation(grayscale);
    ***/
    transformation(fade);

    // Position
    transformation(translate);
    transformation(move);

    // Other
    transformation(overlay);
    transformation(repeat);
    transformation(zoom);

    /***
        TODO: transformation(concat);
        TODO: transformation(merge);
    ***/

    static const std::map<std::string, std::function<void(std::shared_ptr<IInput>, Register &, const json::object_t &)>> map{
        // Color
        {"fade", fade},
        // Position
        {"translate", translate},
        {"move", move},
        // Other
        {"overlay", overlay},
        {"repeat", repeat},
        {"zoom", zoom},
    };
}
