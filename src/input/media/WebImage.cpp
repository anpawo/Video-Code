/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Image
*/

#include "input/media/WebImage.hpp"

#include <cpr/cpr.h>
#include <opencv2/core/hal/interface.h>

#include <opencv2/core/mat.hpp>
#include <opencv2/imgcodecs.hpp>
#include <utility>
#include <vector>

#include "opencv2/imgproc.hpp"
#include "utils/Exception.hpp"

WebImage::WebImage(json::object_t&& args)
    : AInput(std::move(args))
{
    construct();
}

void WebImage::construct()
{
    std::string url = _args.at("url");

    cpr::Response response = cpr::Get(cpr::Url{url});

    if (response.status_code != 200) {
        throw Error("Could not load Image from the url: " + url);
    }

    std::vector<uchar> buffer(response.text.begin(), response.text.end());
    cv::Mat mat = cv::imdecode(buffer, cv::IMREAD_UNCHANGED);

    if (mat.empty()) {
        throw Error("Could not load Image: " + url);
    }

    if (mat.channels() != 4) {
        cv::cvtColor(mat, mat, cv::COLOR_BGR2BGRA);
    }

    setBase(std::move(mat));
}

// TODO: add stack that keeps image in track
