/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** translate
*/

#include "transformation/transformation.hpp"

void transformation::move(IterableInput input, const json::object_t& args)
{
    const int dstX = args.at("x");
    const int dstY = args.at("y");
    const int srcX = input.get()->begin()->_meta.x;
    const int srcY = input.get()->begin()->_meta.y;
    const int nbFrames = input._nbFrames;

    if (nbFrames == 0) {
        return;
    }

    const float velX = (dstX - srcX) / static_cast<float>(nbFrames);
    const float velY = (dstY - srcY) / static_cast<float>(nbFrames);

    int index = 1;
    for (auto& [_, meta] : input) {
        meta.x += velX * index;
        meta.y += velY * index;
        index += 1;
    }
}
