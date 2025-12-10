/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Text
*/

#include "input/shape/Circle.hpp"

#include <vector>

#include "input/Frame.hpp"
#include "opencv2/core/types.hpp"
#include "opencv2/imgproc.hpp"

Circle::Circle(json::object_t &&args)
    : AInput(
          std::move(args),
          {
              "radius",
              "thickness",
              "color",
              "filled",
          }
      )
{
    construct();
}

void Circle::construct()
{
    int radius = _args.at("radius");
    int thickness = _args.at("thickness");
    const std::vector<int> &color = _args.at("color");
    bool filled = _args.at("filled");

    if (thickness == 0) {
        thickness = 1;
    }

    cv::Mat mat = cv::Mat(radius * 2, radius * 2, CV_8UC4).setTo(cv::Scalar(0, 0, 0, 0));

    cv::circle(mat, cv::Point(radius, radius), radius - thickness / 2 * !filled, cv::Scalar(color[2], color[1], color[0], color[3]), filled ? cv::FILLED : thickness, cv::LINE_AA);

    setBase(std::move(mat));
}
