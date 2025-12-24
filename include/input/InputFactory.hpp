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
// #include "input/media/Video.hpp"
// #include "input/media/WebImage.hpp"
#include "input/shape/Circle.hpp"
#include "input/shape/Rectangle.hpp"
// #include "input/text/Text.hpp"

using json = nlohmann::json;

#define input(i) {#i, [](json::object_t &&args) -> std::unique_ptr<IInput> { return std::make_unique<i>(std::move(args)); }}

namespace Factory
{

    ///< Each instruction
    const std::map<std::string, std::function<std::unique_ptr<IInput>(json::object_t &&)>> inputs{
        ///< Media
        input(Image),
        // input(Video),

        ///< Web Media
        // input(WebImage),

        ///< Text
        // input(Text),

        ///< Shape
        input(Rectangle),
        input(Circle),
    };
};
