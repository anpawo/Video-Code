/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** color
*/

#pragma once

#include <nlohmann/json.hpp>

#include "input/Iterable.hpp"
#include "vm/Register.hpp"

using json = nlohmann::json;

#define transformation(t) void t(IterableInput input, const json::object_t &args)

namespace transformation
{

    //< Color
    transformation(grayscale);
    transformation(fade);

    //< Position
    transformation(move);
    transformation(setPosition);

    //< Other
    transformation(repeat);
    transformation(zoom);
    transformation(scale);

    /***
        TODO: transformation(concat);
        TODO: transformation(merge);
    ***/

    ///< Setter
    /***
        TODO: transformation(setOpacity);
    ***/

    static const std::map<std::string, std::function<void(IterableInput input, const json::object_t &args)>> map{
        //< Color
        {"grayscale", grayscale},
        {"fade", fade},
        //< Position
        {"setPosition", setPosition},
        {"move", move},
        //< Other
        {"repeat", repeat},
        {"zoom", zoom},
        {"scale", scale},
    };
}
