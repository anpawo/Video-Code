/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Core
*/

#pragma once

#include <QLabel>
#include <argparse/argparse.hpp>
#include <opencv2/opencv.hpp>

#include "input/IInput.hpp"

namespace VC
{
    class Core
    {
    public:

        Core(const argparse::ArgumentParser& parser);
        ~Core();

        ///< Reload the source file, then execute the stack, then add the new frames to the Timeline.
        void reloadSourceFile();
        void executeStack();
        void addNewFrames();

        ///< Update the current frame being displayed in the window
        void updateFrame(QLabel& imageLabel);

        ///< Generate the video
        int generateVideo();

    private:

        ///< Window size
        const int _width;
        const int _height;

        ///< Framerate of the video
        const int _framerate;

        ///< Source file
        const std::string _sourceFile;
        ///< Output file
        const std::string _outputFile;

        ///< Background frame, black with alpha 0
        const cv::Mat _bgFrame;

        ///< Index of the frame currently being displayed
        std::size_t _index{0};

        ///< The video editor is paused
        bool _paused{false};

        ///< All frames composing the video, they are called the Timeline.
        std::vector<cv::Mat> _frames{};

        ///< Inputs created
        std::vector<std::shared_ptr<IInput>> _inputs{};

        ///< Inputs showed
        std::vector<size_t> _addedInputs{};

        ///< Stack containing the steps of the video
        json::array_t _stack{};
    };
};
