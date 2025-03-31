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
#include <vector>

#include "input/IInput.hpp"
#include "input/composition/Group.hpp"
#include "input/media/Image.hpp"
#include "input/media/Video.hpp"
#include "input/shape/Circle.hpp"
#include "input/shape/Rectangle.hpp"
#include "input/text/Text.hpp"

using json = nlohmann::json;

#define input(i) {#i, [](json::object_t &&args) { return std::make_shared<i>(std::move(args)); }}
#define composite(i, f) {#i, [](std::vector<std::shared_ptr<IInput>> &inputs, json::object_t &&args) { return f; }}

namespace Factory
{

    ///< Each instruction
    const std::map<std::string, std::function<std::shared_ptr<IInput>(json::object_t &&)>> concrete{
        ///< Media
        input(Image),
        input(Video),

        ///< Text
        input(Text),

        ///< Shape
        input(Rectangle),
        input(Circle),

        // /// TODO: Formula (not important)
    };

    const std::map<std::string, std::function<std::shared_ptr<IInput>(std::vector<std::shared_ptr<IInput>> &, json::object_t &&)>> composite{
        // composite(Copy, std::shared_ptr<IInput>(inputs[args.at("input")]->copy())),

        composite(Group, std::make_shared<Group>(inputs, std::move(args))),

        // composite(Slice, std::make_shared<Slice>(inputs[args.at("input")], args.at("start"), args.at("stop"))),
    };

    ///< Create a new `Input`
    inline std::shared_ptr<IInput> create(const std::string &type, json::object_t args, std::vector<std::shared_ptr<IInput>> &inputs)
    {
        if (concrete.find(type) != concrete.end()) {
            return concrete.at(type)(std::move(args));
        }
        else {
            return composite.at(type)(inputs, std::move(args));
        }
    }
};
