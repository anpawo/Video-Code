/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** translate
*/

#include <memory>

#include "transformation/transformation.hpp"
#include "vm/Register.hpp"

void transformation::overlay(std::shared_ptr<IInput> input, Register &reg, const json::array_t &args)
{
    auto input1 = input;
    auto input2 = reg[args[0]];

    const std::vector<cv::Mat> &bg = input1->getFrames();
    const std::vector<cv::Mat> &ov = input2->getFrames();

    std::vector<cv::Mat> frames;
    std::size_t bgNbFrames = bg.size();
    std::size_t ovNbFrames = ov.size();
    std::size_t nbFrames = std::max(bgNbFrames, ovNbFrames);

    for (std::size_t i = 0; i < nbFrames; i++)
    {
        if (i >= ovNbFrames)
        {
            frames.push_back(bg[i].clone());
        } else if (i >= bgNbFrames)
        {
            frames.push_back(ov[i].clone());
        } else
        {
            int nbRows = std::max(bg[i].rows, ov[i].rows);
            int nbCols = std::max(bg[i].cols, ov[i].cols);

            cv::Mat f(nbRows, nbCols, CV_8UC4);

            for (int iy = 0; iy < nbRows; iy++)
            {
                for (int ix = 0; ix < nbCols; ix++)
                {
                    cv::Vec4b pBg = (iy < bg[i].rows && ix < bg[i].cols) ? bg[i].at<cv::Vec4b>(iy, ix) : cv::Vec4b(0, 0, 0, 0);
                    cv::Vec4b pOv = (iy < ov[i].rows && ix < ov[i].cols) ? ov[i].at<cv::Vec4b>(iy, ix) : cv::Vec4b(0, 0, 0, 0);

                    float alphaOv = pOv[3] / 255.0f;

                    cv::Vec4b blended;
                    for (int c = 0; c < 3; c++)
                    {
                        blended[c] = static_cast<uchar>(pOv[c] * alphaOv + pBg[c] * (1.0f - alphaOv));
                    }
                    blended[3] = std::max(pBg[3], pOv[3]);

                    f.at<cv::Vec4b>(iy, ix) = blended;
                }
            }
            frames.push_back(f);
        }
    }

    input1->getFrames() = std::move(frames);
}
