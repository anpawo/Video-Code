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
    const float factor = args.at("factor");
    size_t start = args.at("start");

    input->addTransformation(start, factor != 1, "scale", [factor](Frame& frame) {
        cv::resize(frame.mat, frame.mat, cv::Size(), factor, factor);
    });
}
