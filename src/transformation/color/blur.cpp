/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** blur
*/

#include <opencv2/core.hpp>
#include <opencv2/opencv.hpp>
#include "transformation/transformation.hpp"

void transformation::blur(std::shared_ptr<IInput>& input, const json::object_t& args)
{
    int strength = args.at("strength");   // 🔴 int, pas float
    size_t start = args.at("start");

    if (strength < 1) strength = 1;
    if (strength % 2 == 0) strength++;    // kernel impair obligatoire

    input->addTransformation(start, strength > 1, "blur",
        [strength](Frame& frame) {
            cv::GaussianBlur(
                frame.mat,
                frame.mat,
                cv::Size(strength, strength),
                0
            );
        }
    );
}
    