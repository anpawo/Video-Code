/*
** EPITECH PROJECT, 2025
** eip [WSL: Ubuntu]
** File description:
** zoom
*/

#include "opencv2/imgproc.hpp"
#include "transformation/transformation.hpp"

void transformation::zoom(IterableInput input, const json::object_t &args)
{
    const int x = args.at("x").is_number_integer() ? args.at("x").get<int>() : args.at("x").get<float>() * input.get()->begin()->mat.cols;
    const int y = args.at("y").is_number_integer() ? args.at("y").get<int>() : args.at("y").get<float>() * input.get()->begin()->mat.rows;
    const cv::Point2f center(x, y);

    const float startFactor = args.at("factor")[0];
    const float endFactor = args.at("factor")[1];

    const float zoomIncr = (endFactor - startFactor) / (input._nbFrames - 1);
    float zoomAcc = startFactor - zoomIncr;

    for (auto &[frame, _] : input) {
        zoomAcc += zoomIncr;
        cv::Mat zoomMatrix = cv::getRotationMatrix2D(center, 0, zoomAcc);
        cv::warpAffine(frame, frame, zoomMatrix, frame.size());
    }
}
