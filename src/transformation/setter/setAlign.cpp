/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** translate
*/

#include "transformation/transformation.hpp"

void transformation::setAlign(std::shared_ptr<IInput>& input, const json::object_t& args)
{
    json x = args.at("x");
    json y = args.at("y");
    size_t start = args.at("start");

    input->addSetter(start, {}, [x, y](json::object_t&, Metadata& meta) {
        if (!x.is_null()) {
            meta.align.x = alignRatio.at(x);
        }
        if (!y.is_null()) {
            meta.align.y = alignRatio.at(y);
        }
    });
}
