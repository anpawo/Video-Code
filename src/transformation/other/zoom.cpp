/*
** EPITECH PROJECT, 2025
** eip [WSL: Ubuntu]
** File description:
** zoom
*/

#include <memory>
#include "input/IInput.hpp"
#include "transformation/transformation.hpp"
#include <iostream>

void transformation::zoom(std::shared_ptr<IInput> input, [[maybe_unused]] Register &reg, const json::object_t &args)
{
    float zoomFactor = args.at("zoomFactor");
    std::pair<float, float> zoomCenter = args.at("zoomCenter");

    for (auto &[frame, _] : *input)
    {
        cv::Mat zoomedFrame;
        cv::Point2f center(frame.cols * zoomCenter.first, frame.rows * zoomCenter.second);
        cv::Mat zoomMatrix = cv::getRotationMatrix2D(center, 0, zoomFactor);
        cv::warpAffine(frame, zoomedFrame, zoomMatrix, frame.size());
        frame = zoomedFrame;
    }
}
