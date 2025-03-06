/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Register
*/

#include "vm/Register.hpp"

void Register::newInput(const std::string& type, const json::object_t& args)
{
    _inputFactory.at(type)(args);
}

std::shared_ptr<IInput> Register::operator[](size_t index)
{
    return _inputs[index];
}

void Register::clear()
{
    _inputs.clear();
}
