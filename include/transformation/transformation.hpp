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
#define bind(n) \
    {           \
        #n, n   \
    }

namespace transformation
{

    ///< Color
    transformation(fade);
    transformation(grayscale);

    ///< Position
    transformation(moveTo);

    ///< Other
    transformation(zoom);
    transformation(scale);

    ///< Setter
    transformation(setPosition);
    transformation(setAlign);
    /***
    TODO: transformation(setOpacity);
    ***/
    transformation(setArgument);

    static const std::map<std::string, std::function<void(std::shared_ptr<IInput> &input, const json::object_t &args)>> map{
        ///< Color
        bind(fade),
        bind(grayscale),

        ///< Position
        bind(moveTo),

        ///< Other
        bind(zoom),
        bind(scale),

        ///< Setter
        bind(setPosition),
        bind(setAlign),
        bind(setArgument),
    };
}
