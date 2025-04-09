/*
** EPITECH PROJECT, 2025
** eip [WSL: Ubuntu]
** File description:
** zoom
*/

#include "opencv2/imgproc.hpp"
#include "transformation/transformation.hpp"

void transformation::zoom(std::shared_ptr<IInput>& input, const json::object_t& args)
{
    const json x = args.at("x");
    const json y = args.at("y");
    const size_t duration = args.at("duration");
    size_t start = args.at("start");

    const float startFactor = args.at("factor")[0];
    const float endFactor = args.at("factor")[1];

    const float zoomIncr = (endFactor - startFactor) / (duration - 1);
    float zoomAcc = startFactor - zoomIncr;

    for (size_t i = 0; i < duration; i++) {
        zoomAcc += zoomIncr;
        input->addTransformation(start + i, [zoomAcc, y, x](Frame& frame) {
            cv::Point2f center(
                x.is_number_integer() ? x.get<int>() : x.get<float>() * frame.mat.cols,
                y.is_number_integer() ? y.get<int>() : y.get<float>() * frame.mat.rows
            );
            cv::Mat zoomMatrix = cv::getRotationMatrix2D(center, 0, zoomAcc);
            cv::warpAffine(frame.mat, frame.mat, zoomMatrix, frame.mat.size());
        });
    }
}
