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

    const float scaleIncr = (endFactor - startFactor) / (input._nbFrames - 1);
    float scaleAcc = startFactor - scaleIncr;

    for (auto &[frame, _] : input) {
        scaleAcc += scaleIncr;
        cv::resize(frame, frame, cv::Size(), scaleAcc, scaleAcc);
    }
}
