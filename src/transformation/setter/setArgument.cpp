/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** translate
*/

#include "transformation/transformation.hpp"

void transformation::setArgument(std::shared_ptr<IInput>& input, const json::object_t& args)
{
    json name = args.at("name");
    json value = args.at("value");
    size_t start = args.at("start");

    input->addSetter(start, [name, value](json::object_t& args) {
        args[name] = value;
    });
}
