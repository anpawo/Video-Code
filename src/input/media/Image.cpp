/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Image
*/

#include "input/media/Image.hpp"

#include <opencv2/core/mat.hpp>
#include <opencv2/imgcodecs.hpp>
#include <utility>

#include "opencv2/imgproc.hpp"
#include "utils/Exception.hpp"

Image::Image(json::object_t&& args)
    : AInput(std::move(args))
{
    std::string filepath = _args.at("filepath");

    cv::Mat mat = cv::imread(filepath);

    if (mat.empty()) {
        throw Error("Could not load Image: " + filepath);
    }

    if (mat.channels() != 4) {
        cv::cvtColor(mat, mat, cv::COLOR_BGR2BGRA);
    }

    _base = std::make_unique<Frame>(std::move(mat));
}
