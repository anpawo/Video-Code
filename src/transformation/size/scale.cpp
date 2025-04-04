/*
** EPITECH PROJECT, 2025
** eip [WSL: Ubuntu]
** File description:
** scale
*/

#include "opencv2/imgproc.hpp"
#include "transformation/transformation.hpp"

void transformation::scale(std::shared_ptr<IInput>& input, const json::object_t& args)
{
    const float startFactor = args.at("factor")[0];
    const float endFactor = args.at("factor")[1];
    const size_t duration = args.at("duration");

    const float scaleIncr = (endFactor - startFactor) / (duration - 1);
    float scaleAcc = startFactor - scaleIncr;

    for (size_t i = 0; i < duration; i++) {
        scaleAcc += scaleIncr;
        input->addTransformation(i, [scaleAcc](Frame& frame) {
            cv::resize(frame.mat, frame.mat, cv::Size(), scaleAcc, scaleAcc);
        });
    }
}
