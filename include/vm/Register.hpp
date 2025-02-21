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
#include "input/Image.hpp"
#include "input/Video.hpp"

using json = nlohmann::json;

class Register
{
public:

    Register() = default;
    ~Register() = default;

    ///< Update instructions
    void updateInstructions(json::array_t &&newInstructions);

    ///< Run the first instruction not done
    void runNextInstruction();

    ///< Access _inputs at `index`
    std::shared_ptr<IInput> operator[](size_t index);

private:

    ///< Variables representing the Inputs currently used in the program
    std::vector<std::shared_ptr<IInput>> _inputs{};

    ///< Instructions to create new Inputs: [[instructionName, {instructionArgs}]]
    json::array_t _instructions{};

    ///< Each instruction
    const std::map<std::string, std::function<void(const json::object_t &)>> _inputFactory{
        {"Image", [this](const json::object_t &args) { _inputs.push_back(std::make_shared<Image>(args.at("filepath"))); }},
        {"Video", [this](const json::object_t &args) { _inputs.push_back(std::make_shared<Video>(args.at("filepath"))); }},
        {"Copy", [this](const json::object_t &args) { _inputs.push_back(std::shared_ptr<IInput>(_inputs[args.at("input")]->copy())); }},
        /// TODO: Shapes (Circle, Square)
        /// TODO: Text (List of char)
        /// TODO: Formula (not important)
    };

    /// TODO: env to keep track of already loaded images. prevent reload everytime
};
