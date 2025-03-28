/*
** EPITECH PROJECT, 2025
** eip [WSL: Ubuntu]
** File description:
** scale
*/

#include "opencv2/imgproc.hpp"
#include "transformation/transformation.hpp"

void transformation::scale(IterableInput input, const json::object_t &args)
{
    const float startFactor = args.at("factor")[0];
    const float endFactor = args.at("factor")[1];

    const bool isCentered = args.at("centered").get<bool>();

    const float scaleIncr = (endFactor - startFactor) / (input._nbFrames - 1);
    float scaleAcc = startFactor - scaleIncr;

    float velX = 0;
    float velY = 0;

    float offsetX = 0;
    float offsetY = 0;

    if (isCentered) {
        const int srcX = input.get()->begin()->meta.position.x;
        const int srcY = input.get()->begin()->meta.position.y;

        const float centerX = srcX + (input.get()->begin()->mat.cols / 2.0);
        const float centerY = srcY + (input.get()->begin()->mat.rows / 2.0);

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
            meta.position.x += velX * index - offsetX;
            meta.position.y += velY * index - offsetY;
        }
        index += 1;
    }
}
