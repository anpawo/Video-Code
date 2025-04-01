/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** translate
*/

#include "transformation/transformation.hpp"

void transformation::moveTo(std::shared_ptr<IInput>& input, const json::object_t& args)
{
    int srcX = args.at("srcX");
    int srcY = args.at("srcY");
    json dstX = args.at("dstX");
    json dstY = args.at("dstY");
    size_t duration = args.at("duration");

    if (duration == 0) {
        return;
    }

    float velX = dstX.is_null() ? 0 : ((dstX.get<int>() - srcX) / (duration - 1.0));
    float velY = dstY.is_null() ? 0 : ((dstY.get<int>() - srcY) / (duration - 1.0));

    for (size_t i = 1; i < duration; i++) {
        input->addTransformation(i, [velX, velY](Frame& f) {
            f.meta.position.x += velX;
            f.meta.position.y += velY;
        });
    }
}
