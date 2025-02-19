/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** translate
*/

#include <memory>

#include "input/IInput.hpp"
#include "opencv2/core.hpp"
#include "transformation/transformation.hpp"
#include "utils/Debug.hpp"

void transformation::translate(std::shared_ptr<IInput> input, [[maybe_unused]] Register &reg, const json::object_t &args)
{
    int x = args.at("x");
    int y = args.at("y");

    VC_LOG_DEBUG("translation")

    for (auto &m : input->getFrames())
    {
        if (x < 0)
        {
            // rm col
            m = m.rowRange(-x, m.rows);
        }
        else if (x > 0)
        {
            // add col
            cv::vconcat(cv::Mat(x, m.cols, CV_8UC4).setTo(cv::Scalar(0, 0, 0, 0)), m, m);
        }
        if (y < 0)
        {
            // rm row
            m = m.colRange(-y, m.cols);
        }
        else if (y > 0)
        {
            // add row
            cv::hconcat(cv::Mat(m.rows, y, CV_8UC4).setTo(cv::Scalar(0, 0, 0, 0)), m, m);
        }
    }
}

// TODO: should have a position
