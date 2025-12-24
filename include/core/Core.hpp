/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Core
*/

#pragma once

#include <QLabel>
#include <argparse/argparse.hpp>
#include <memory>
#include <opencv2/opencv.hpp>

#include "input/IInput.hpp"

namespace VC
{
    class Core
    {
    public:

        Core(const argparse::ArgumentParser& parser);
        ~Core() = default;

        ///< Reload the source file, then execute the stack, then add the new frames to the Timeline.
        void reloadSourceFile();
        std::string serializeScene();
        void executeStack();
        cv::Mat generateFrame(int index);

        ///< Update the current frame being displayed in the window
        void updateFrame(QLabel& imageLabel);

        ///< Generate the video
        int generateVideo();

        ///< Time control
        void pause();
        void goToFirstFrame();
        void goToLastFrame();
        void forward1frame();
        void backward1frame();

    private:

        ///< Window size
        const int _width;
        const int _height;

        ///< Framerate of the video
        const size_t _framerate;

        ///< Source & Output file
        const std::string _sourceFile;
        const std::string _outputFile;

        ///< Information display
        const bool _showstack;
        const bool _timeit;

        ///< Background frame, black with alpha 0
        const cv::Mat _bgFrame;

        ///< Index of the frame currently being displayed
        size_t _index{0};
        size_t _nbFrame{1}; // Starting at 1 forces the first frame to be generated even without any transformations.

        ///< The video editor is paused
        bool _paused{false};
        bool _indexChanged{true};

        ///< Inputs created
        std::vector<std::unique_ptr<IInput>> _inputs{};

        ///< Stack containing the steps of the video
        json::array_t _stack{};
    };
};
