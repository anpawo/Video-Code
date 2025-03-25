/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Register
*/

#pragma once

#include <cstddef>
#include <map>
#include <memory>
#include <nlohmann/json.hpp>
#include <string>
#include <vector>

#include "input/IInput.hpp"
#include "input/composite/Slice.hpp"
#include "input/concrete/media/Image.hpp"
#include "input/concrete/media/Video.hpp"
#include "input/concrete/shape/Circle.hpp"
#include "input/concrete/shape/Rectangle.hpp"
#include "input/concrete/text/Text.hpp"

using json = nlohmann::json;

class Register
{
public:

    Register() = default;
    ~Register() = default;

    ///< Create a new `Input`
    void newInput(const std::string &type, const json::object_t &args);

    ///< Access _inputs at `index`
    std::shared_ptr<IInput> operator[](size_t index);

    ///< Remove old `Inputs`
    void clear();

private:

    ///< frame rate
    const int _framerate{24};

    ///< Variables representing the Inputs currently used in the program
    std::vector<std::shared_ptr<IInput>> _inputs{};

    ///< Each instruction
    const std::map<std::string, std::function<void(const json::object_t &)>> _inputFactory{
        {"Image", [this](const json::object_t &args) { _inputs.push_back(std::make_shared<Image>(args.at("filepath"))); }},
        {"Video", [this](const json::object_t &args) { _inputs.push_back(std::make_shared<Video>(args.at("filepath"))); }},
        {"Copy", [this](const json::object_t &args) { _inputs.push_back(std::shared_ptr<IInput>(_inputs[args.at("input")]->copy())); }},
        {"Slice", [this](const json::object_t &args) { _inputs.push_back(std::make_shared<Slice>(_inputs[args.at("input")], args.at("start"), args.at("stop"))); }},
        {"Text", [this](const json::object_t &args) { _inputs.push_back(std::make_shared<Text>(args.at("text"), args.at("fontSize"), args.at("fontThickness"), args.at("color"), args.at("duration"), _framerate)); }},
        ///< Shapes
        {"Circle", [this](const json::object_t &args) { _inputs.push_back(std::make_shared<Circle>(args, _framerate)); }},
        {"Rectangle", [this](const json::object_t &args) { _inputs.push_back(std::make_shared<Rectangle>(args, _framerate)); }},
        /// TODO: Square
        /// TODO: Formula (not important)
    };

    /// TODO: env to keep track of already loaded images. prevent reload everytime
};
