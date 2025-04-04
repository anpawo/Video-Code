/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** fade
*/
#include <opencv2/opencv.hpp>

#include "opencv2/core/matx.hpp"
#include "transformation/transformation.hpp"

void transformation::fade(std::shared_ptr<IInput>& input, const json::object_t& args)
{
    const json::array_t& sides = args.at("sides");
    bool affectTransparentPixel = args.at("affectTransparentPixel");
    float startOpacity = args.at("startOpacity");
    float endOpacity = args.at("endOpacity");
    size_t duration = args.at("duration");

    for (size_t i = 0; i < duration; i++) {
        input->addTransformation(i, [affectTransparentPixel, sides, i, duration, startOpacity, endOpacity](Frame& frame) {
            float opacity = startOpacity + (endOpacity - startOpacity) * (static_cast<float>(i) / (duration - 1));
            const auto& cols = frame.mat.cols;
            const auto& rows = frame.mat.rows;

            for (int y = 0; y < rows; y++) {
                for (int x = 0; x < cols; x++) {
                    if (frame.mat.at<cv::Vec4b>(y, x)[3] == 0 && affectTransparentPixel == false) {
                        continue;
                    }

                    for (const auto& side : sides) {
                        if (side == "left") {
                            if (cols > 1) {
                                opacity *= 1 - static_cast<float>(x) / (cols - 1) * (1 - i / (duration - 1.0));
                            }
                        }
                        else if (side == "right") {
                            if (cols > 1) {
                                ///< FIX: maybe error. try with fadeIn from Left then fadeOut from Right
                                opacity *= 1 - static_cast<float>(cols - 1 - x) / (cols - 1) * (1 - i / (duration - 1.0));
                            }
                        }
                        else if (side == "up") {
                            if (rows > 1) {
                                opacity *= 1 - static_cast<float>(y) / (rows - 1) * (1 - i / (duration - 1.0));
                            }
                        }
                        else if (side == "down") {
                            if (rows > 1) {
                                opacity *= 1 - static_cast<float>(rows - 1 - y) / (rows - 1) * (1 - i / (duration - 1.0));
                            }
                        }
                    }

                    frame.mat.at<cv::Vec4b>(y, x)[3] = static_cast<unsigned char>(std::clamp<float>(opacity, 0.0f, 255.0f));
                }
            }
        });
    }
}
