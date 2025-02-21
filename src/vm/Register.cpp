/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Register
*/

#include "vm/Register.hpp"

#include <utility>

void Register::updateInstructions(json::array_t&& newInstructions)
{
    _instructions = std::forward<json::array_t>(newInstructions);

    /// TODO: cache
    _inputs.clear();
}

void Register::runNextInstruction()
{
    _inputFactory.at(_instructions[_inputs.size()]["type"])(_instructions[_inputs.size()]);
}

std::shared_ptr<IInput> Register::operator[](size_t index)
{
    while (_inputs.size() <= index)
    {
        runNextInstruction();
    }

    return _inputs[index];
}
