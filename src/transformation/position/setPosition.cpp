/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** translate
*/

#include "transformation/transformation.hpp"

void transformation::setPosition(IterableInput input, const json::object_t& args)
{
    json x = args.at("x");
    json y = args.at("y");

    for (auto& [_, meta] : input) {
        if (!x.is_null()) {
            if (x.is_number_integer()) {
                meta.x = x;
            }
            else {
                meta.x = 1920 * x.get<float>();
            }
        }
        if (!y.is_null()) {
            if (y.is_number_integer()) {
                meta.y = y;
            }
            else {
                meta.y = 1080 * y.get<float>();
            }
        }
    }
}
