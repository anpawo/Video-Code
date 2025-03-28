/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Image
*/

#include "input/concrete/media/Image.hpp"

#include <opencv2/core/mat.hpp>
#include <opencv2/imgcodecs.hpp>
#include <utility>
#include <vector>

#include "input/concrete/ABCConcreteInput.hpp"
#include "opencv2/imgproc.hpp"
#include "utils/Exception.hpp"

Image::Image(json::object_t&& args)
    : ABCConcreteInput(std::move(args))
{
    std::string filepath = _args.at("filepath");

    cv::Mat image = cv::imread(filepath);

    if (image.empty()) {
        throw Error("Could not load Image: " + filepath);
    }

    if (image.channels() != 4) {
        cv::cvtColor(image, image, cv::COLOR_BGR2BGRA);
    }

    _frames.push_back(Frame(std::move(image)));
}
