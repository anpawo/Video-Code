/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** LiveWindow
*/

#pragma once

#include <qapplication.h>
#include <qwidget.h>

#include <cstddef>
#include <functional>
#include <map>
#include <memory>
#include <nlohmann/json.hpp>
#include <opencv2/core/mat.hpp>
#include <string>
#include <vector>

#include "input/IInput.hpp"
#include "qlabel.h"
#include "qnamespace.h"
#include "vm/AppWindow.hpp"
#include "vm/Register.hpp"

#define bindCmd(x) ([this]() { this->x(); })

using json = nlohmann::json;

class VideoCode
{
public:

    VideoCode(int argc, char **argv, int width, int height, std::string sourceFile, bool generate, std::string outputFile);

    ///< Start the program
    int run();

    ///< Called every loop iteration to update the current frame being displayed
    void updateFrame(QLabel &imageLabel);

    ///< Set the index of the timeline to a label
    void goToLabel(const std::string &label);

    ///< Add a label
    void addLabel(const std::string &label, std::size_t index);

    ///< Remove a label
    void removeLabel(const std::string &index);

    ///< Add a frame to the timeline
    void addFrame(const cv::Mat &mat, const Metadata &meta);
    void addFrames(const std::shared_ptr<IInput> input);

    ///< Events >///
    void pause();
    void stop();
    void reloadSourceFile(); ///< Update the timeline if any changes occured in the source file
    void goToFirstFrame();
    void goToLastFrame();
    void goToPreviousLabel();
    void goToNextLabel();

    ///< Execute the instructions in the stack
    void executeStack();

private:

    ///< TODO: frame rate
    const int _frameRate{24};

    ///< Window size
    const int _width;
    const int _height;

    ///< source file
    const std::string _sourceFile;

    ///< Black frame for empty timelines
    const cv::Mat _defaultBlackFrame;

    ///< Current index of the frame of the timeline being displayed
    std::size_t _index{0};

    ///< Timeline representing all frames
    std::vector<cv::Mat> _frames{};

    ///< Default initial label
    const std::string _initialLabel{"__start"};

    ///< Label currently playing
    std::string _currentLabel{_initialLabel};

    ///< Labels are timestamp of the Timeline
    std::map<std::string, std::size_t> _labels{{_initialLabel, 0}};
    std::map<std::size_t, std::string> _labelsByVal{{0, _initialLabel}};

    // clang-format off
    ///< Events
    const std::map<int, std::function<void()>> _events{
        {Qt::Key_Space,     bindCmd(pause)},
        {Qt::Key_Escape,    bindCmd(stop)},            
        {Qt::Key_R,         bindCmd(reloadSourceFile)},
        {Qt::Key_Down,      bindCmd(goToFirstFrame)},
        {Qt::Key_Up,        bindCmd(goToLastFrame)},
        {Qt::Key_Left,      bindCmd(goToPreviousLabel)},   
        {Qt::Key_Right,     bindCmd(goToNextLabel)},       
    };
    // clang-format on

    ///< Timeline paused
    bool _paused{true};

    ///< Timeline running
    bool _running{true};

    ///< Register handling the Inputs
    Register _register{};

    ///< Stack containing the transformations to apply to the Inputs
    json::array_t _actionStack{};

    ///< Window to modify the video in real time
    std::unique_ptr<AppWindow> _app{nullptr};

    ///< Output File for the generation
    std::string _outputFile;
};
