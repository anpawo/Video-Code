/*
** EPITECH PROJECT, 2025
** eip [WSL: Ubuntu]
** File description:
** scale
*/

#include "transformation/transformation.hpp"

void transformation::scale(IterableInput input, const json::object_t &args)
{
    const float startFactor = args.at("factor")[0];
    const float endFactor = args.at("factor")[1];

    const bool isCentered = args.at("mode") == "Center";

    const float scaleIncr = (endFactor - startFactor) / (input._nbFrames - 1);
    float scaleAcc = startFactor - scaleIncr;

    float velX = 0;
    float velY = 0;

    float offsetX = 0;
    float offsetY = 0;

    if (isCentered) {
        const int srcX = input.get()->begin()->_meta.x;
        const int srcY = input.get()->begin()->_meta.y;

        const float centerX = srcX + (input.get()->begin()->_mat.cols / 2);
        const float centerY = srcY + (input.get()->begin()->_mat.rows / 2);

        const float moveX = startFactor <= endFactor ? (srcX - centerX) : (centerX - srcX);
        const float moveY = startFactor <= endFactor ? (srcY - centerY) : (centerY - srcY);

        velX = moveX / static_cast<float>(input._nbFrames);
        velY = moveY / static_cast<float>(input._nbFrames);

        if (startFactor < endFactor) {
            offsetX = velX * input._nbFrames;
            offsetY = velY * input._nbFrames;
        }
    }

    int index = 1;
    for (auto &[frame, meta] : input) {
        scaleAcc += scaleIncr;
        cv::resize(frame, frame, cv::Size(), scaleAcc, scaleAcc);
        if (isCentered) {
            meta.x += velX * index - offsetX;
            meta.y += velY * index - offsetY;
        }
        index += 1;
    }
}
