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

#define transformation(t) void t(std::shared_ptr<IInput> input, Register &reg, const json::array_t &args)

namespace transformation
{

    // Color
    // TODO: transformation(grayscale);
    // TODO: transformation(fade);

    // Position
    transformation(translate);
    /***
        TODO: transformation(move);
    ***/

    // Other
    transformation(overlay);
    /***
        transformation(repeat);
        transformation(wait);
        transformation(concat);
        transformation(merge);
    ***/

    static const std::map<std::string, std::function<void(std::shared_ptr<IInput>, Register &, const json::array_t &)>> map{
        // {"grayscale", grayscale},
        // {"fade", fade},
        {"translate", translate},
        {"overlay", overlay},
    };
};
