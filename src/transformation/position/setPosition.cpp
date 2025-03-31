/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** translate
*/

#include "transformation/transformation.hpp"

void transformation::setPosition(std::shared_ptr<IInput> input, const json::object_t& args)
{
    json x = args.at("x");
    json y = args.at("y");

    // input->addTransformation([x, y](Frame& frame) {
    //     auto& meta = frame.meta;

    // if (!x.is_null()) {
    //     if (x.is_number_integer()) {
    //         meta.position.x = x;
    //     }
    //     else {
    //         meta.position.x = 1920 * x.get<float>();
    //     }
    // }
    // if (!y.is_null()) {
    //     if (y.is_number_integer()) {
    //         meta.position.y = y;
    //     }
    //     else {
    //         meta.position.y = 1080 * y.get<float>();
    //     }
    // }
    // });
}
