/*
** EPITECH PROJECT, 2025
** eip [WSL: Ubuntu]
** File description:
** zoom
*/

#include <memory>

#include "input/IInput.hpp"
#include "transformation/transformation.hpp"

void transformation::zoom(std::shared_ptr<IInput> input, [[maybe_unused]] Register &reg, const json::object_t &args)
{
    const float zoomFactor = args.at("zoomFactor");
    const std::pair<float, float> zoomCenter = args.at("zoomCenter");
    const bool staticZoom = args.at("mode") == "static";
    const float startZoomFactor = args.at("zoomstart");
    const float endZoomFactor = args.at("zoomend");
    const int nbFrames = input->size();
    int i = 0;

    for (auto &[frame, _] : *input)
    {
        float currentZoomFactor;

        if (staticZoom)
            currentZoomFactor = zoomFactor;
        else
            currentZoomFactor = startZoomFactor + (endZoomFactor - startZoomFactor) * (static_cast<float>(i) / (nbFrames - 1));

        cv::Mat zoomedFrame;
        cv::Point2f center(frame.cols * zoomCenter.first, frame.rows * zoomCenter.second);
        cv::Mat zoomMatrix = cv::getRotationMatrix2D(center, 0, currentZoomFactor);
        cv::warpAffine(frame, zoomedFrame, zoomMatrix, frame.size());
        frame = zoomedFrame;
        i++;
    }
}
