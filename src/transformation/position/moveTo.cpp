/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** translate
*/

#include "transformation/transformation.hpp"

void transformation::moveTo(std::shared_ptr<IInput>& input, const json::object_t& args)
{
    int dstX = args.at("x");
    int dstY = args.at("y");
    int srcX = input->getLastFrame().meta.position.x;
    int srcY = input->getLastFrame().meta.position.y;
    size_t duration = args.at("duration");

    if (duration == 0) {
        return;
    }

    float velX = (dstX - srcX) / (duration - 1.0);
    float velY = (dstY - srcY) / (duration - 1.0);

    float x = srcX;
    float y = srcY;

    for (size_t i = 1; i < duration; i++) {
        x += velX;
        y += velY;
        input->addTransformation(i, [x, y](Frame& f) {
            f.meta.position.x = x;
            f.meta.position.y = y;
        });
    }
}
