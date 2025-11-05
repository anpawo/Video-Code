/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Register
*/

#pragma once

#include <map>
#include <memory>
#include <nlohmann/json.hpp>
#include <string>

#include "input/IInput.hpp"
#include "input/media/Image.hpp"
#include "input/media/Video.hpp"
#include "input/media/WebImage.hpp"
#include "input/shape/Circle.hpp"
#include "input/shape/Rectangle.hpp"
#include "input/text/Text.hpp"

using json = nlohmann::json;

#define input(i) {#i, [](json::object_t &&args) { return std::make_shared<i>(std::move(args)); }}

namespace Factory
{

    ///< Each instruction
    const std::map<std::string, std::function<std::shared_ptr<IInput>(json::object_t &&)>> existingInputs{
        ///< Media
        input(Image),
        input(Video),

        ///< Web Media
        input(WebImage),

        ///< Text
        input(Text),

        ///< Shape
        input(Rectangle),
        input(Circle),

        // /// TODO: Formula (not important)
    };

    ///< Create a new `Input`
    inline std::shared_ptr<IInput> create(const std::string &type, json::object_t args)
    {
        return existingInputs.at(type)(std::move(args));
    }
};
