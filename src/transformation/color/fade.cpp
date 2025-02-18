/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** fade
*/

#include "transformation/transformation.hpp"

std::shared_ptr<_IInput> transformation::fade(std::shared_ptr<_IInput> input, const json::array_t &args)
{
    int nbFrames = input->cgetFrames().size();
    std::string side = args[0];
    int duration = args[1];

    if (duration < 0) {
        duration += nbFrames + 1;
    }

    if (side == "LEFT") {

        for (int n = 0; n < nbFrames; n++) {
            ///< don't affect frames after duration
            if (n >= duration) {
                break;
            }

            // current frame
            auto &m = input->getFrames()[n];

            for (int i = 0; i < m.cols; i++) {
                float progress = i / static_cast<float>(m.cols) / 10;

                // We want to ensure the fade finishes when n == duration
                float mul = std::min(1.0f, static_cast<float>(n) / static_cast<float>(duration) + progress);

                m.col(m.cols - 1 - i).forEach<cv::Vec4b>([mul](cv::Vec4b &pixel, const int *) {
                    pixel[3] *= mul; ///< ensure that many tranformations can be done at the same time
                });
            }
        }
    } else if (side == "RIGHT") {

        for (int n = 0; n < nbFrames; n++) {
            ///< don't affect frames after duration
            if (n >= duration) {
                break;
            }

            // current frame
            auto &m = input->getFrames()[n];

            for (int i = 0; i < m.cols; i++) {
                float progress = i / static_cast<float>(m.cols) / 10;

                // We want to ensure the fade finishes when n == duration
                float mul = std::min(1.0f, static_cast<float>(n) / static_cast<float>(duration) + progress);

                m.col(i).forEach<cv::Vec4b>([mul](cv::Vec4b &pixel, const int *) {
                    pixel[3] *= mul; ///< ensure that many tranformations can be done at the same time
                });
            }
        }
    } else if (side == "DOWN") {
        for (int n = 0; n < nbFrames; n++) {
            ///< don't affect frames after duration
            if (n >= duration) {
                break;
            }

            // current frame
            auto &m = input->getFrames()[n];

            for (int i = 0; i < m.rows; i++) {
                float progress = i / static_cast<float>(m.rows) / 10;

                // We want to ensure the fade finishes when n == duration
                float mul = std::min(1.0f, static_cast<float>(n) / static_cast<float>(duration) + progress);

                m.row(i).forEach<cv::Vec4b>([mul](cv::Vec4b &pixel, const int *) {
                    pixel[3] *= mul; ///< ensure that many tranformations can be done at the same time
                });
            }
        }
    } else if (side == "UP") {
        for (int n = 0; n < nbFrames; n++) {
            ///< don't affect frames after duration
            if (n >= duration) {
                break;
            }

            // current frame
            auto &m = input->getFrames()[n];

            for (int i = 0; i < m.rows; i++) {
                float progress = i / static_cast<float>(m.rows) / 10;

                // We want to ensure the fade finishes when n == duration
                float mul = std::min(1.0f, static_cast<float>(n) / static_cast<float>(duration) + progress);

                m.row(m.rows - 1 - i).forEach<cv::Vec4b>([mul](cv::Vec4b &pixel, const int *) {
                    pixel[3] *= mul; ///< ensure that many tranformations can be done at the same time
                });
            }
        }
    } else if (side == "ALL") {
        for (int n = 0; n < nbFrames; n++) {
            ///< don't affect frames after duration
            if (n >= duration) {
                break;
            }

            // current frame
            auto &m = input->getFrames()[n];

            for (int i = 0; i < m.rows; i++) {
                // We want to ensure the fade finishes when n == duration
                float mul = std::min(1.0f, static_cast<float>(n) / static_cast<float>(duration));

                m.row(m.rows - 1 - i).forEach<cv::Vec4b>([mul](cv::Vec4b &pixel, const int *) {
                    pixel[3] *= mul; ///< ensure that many tranformations can be done at the same time
                });
            }
        }
    }

    return input;
}
