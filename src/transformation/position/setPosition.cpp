/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** translate
*/

#include "transformation/transformation.hpp"

void transformation::setPosition(std::shared_ptr<IInput>& input, const json::object_t& args)
{
    json x = args.at("x");
    json y = args.at("y");

    auto& meta = input->getLastFrame().meta;

    if (!x.is_null()) {
        meta.position.x = x;
    }
    if (!y.is_null()) {
        meta.position.y = y;
    }
}
