/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** fade
*/
#include <algorithm>
#include <opencv2/opencv.hpp>

#include "transformation/transformation.hpp"

void transformation::fade(std::shared_ptr<IInput> input, [[maybe_unused]] Register& reg, const json::object_t& args)
{
    const json::array_t& sides = args.at("sides");
    const int nbFrames = input->size();
    const float startOpacity = args.at("startOpacity");
    const float endOpacity = args.at("endOpacity");
    const bool affectTransparentPixel = args.at("affectTransparentPixel");

    int frameIndex = 0;
    for (auto& [frame, _] : *input)
    {
        int cols = frame.cols;
        int rows = frame.rows;
        float currentOpacity = startOpacity + (endOpacity - startOpacity) * (static_cast<float>(frameIndex) / (nbFrames - 1));

        for (int y = 0; y < rows; y++)
        {
            for (int x = 0; x < cols; x++)
            {
                if (frame.at<cv::Vec4b>(y, x)[3] == 0 && affectTransparentPixel == false)
                {
                    continue;
                }

                float alpha = currentOpacity;

                for (const auto& side : sides)
                {
                    if (side == "left")
                    {
                        if (cols > 1)
                        {
                            alpha *= 1 - static_cast<float>(x) / (cols - 1) * (1 - static_cast<float>(frameIndex) / (nbFrames - 1));
                        }
                    }
                    else if (side == "right")
                    {
                        if (cols > 1)
                        {
                            alpha *= 1 - static_cast<float>(cols - 1 - x) / (cols - 1) * (1 - static_cast<float>(frameIndex) / (nbFrames - 1));
                        }
                    }
                    else if (side == "up")
                    {
                        if (rows > 1)
                        {
                            alpha *= 1 - static_cast<float>(y) / (rows - 1) * (1 - static_cast<float>(frameIndex) / (nbFrames - 1));
                        }
                    }
                    else if (side == "down")
                    {
                        if (rows > 1)
                        {
                            alpha *= 1 - static_cast<float>(rows - 1 - y) / (rows - 1) * (1 - static_cast<float>(frameIndex) / (nbFrames - 1));
                        }
                    }
                }

                frame.at<cv::Vec4b>(y, x)[3] = static_cast<unsigned char>(std::clamp<float>(alpha, 0.0f, 255.0f));
            }
        }
        frameIndex++;
    }
}
