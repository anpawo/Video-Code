/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** color
*/

#pragma once

#include <memory>
#include <nlohmann/json.hpp>

#include "input/IInput.hpp"

using json = nlohmann::json;

#define transformation(t) void t(std::shared_ptr<IInput> &input, const json::object_t &args)
#define bind(n) {#n, n}

namespace transformation
{

    // //< Color
    // transformation(grayscale);
    // transformation(fade);

    // //< Position
    transformation(setPosition);
    transformation(moveTo);

    // //< Other
    // transformation(repeat);
    // transformation(zoom);
    // transformation(scale);

    /***
        TODO: transformation(concat);
        TODO: transformation(merge);
    ***/

    ///< Setter
    /***
        TODO: transformation(setOpacity);
    ***/

    static const std::map<std::string, std::function<void(std::shared_ptr<IInput> &input, const json::object_t &args)>> map{
        //< Color
        // {"grayscale", grayscale},
        // {"fade", fade},
        //< Position
        bind(setPosition),
        bind(moveTo),
        //< Other
        // {"repeat", repeat},
        // {"zoom", zoom},
        // {"scale", scale},
    };
}
