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
    size_t start = args.at("start");

    input->addSetter(start, "setPosition", [x, y](json::object_t& _, Metadata& meta) {
        if (!x.is_null()) {
            meta.position.x = x;
        }
        if (!y.is_null()) {
            meta.position.y = y;
        }
    });
}
