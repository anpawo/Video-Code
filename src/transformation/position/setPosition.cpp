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
    size_t w = args.at("width");
    size_t h = args.at("height");

    auto& meta = input->getLastFrame().meta;

    if (!x.is_null()) {
        if (x.is_number_integer()) {
            meta.position.x = x;
        }
        else {
            meta.position.x = w * x.get<float>();
        }
    }
    if (!y.is_null()) {
        if (y.is_number_integer()) {
            meta.position.y = y;
        }
        else {
            meta.position.y = h * y.get<float>();
        }
    }
}
