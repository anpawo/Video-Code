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
#include "vm/Factory.hpp"

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

    ///< Events >///
    void pause();
    void stop();
    void reloadSourceFile(); ///< Update the timeline if any changes occured in the source file
    void goToFirstFrame();
    void goToLastFrame();
    void backward3frame();
    void forward3frame();

    ///< Execute the instructions in the stack
    void executeStack();

    ///< Update the frames by displaying the newly generated Inputs
    void addNewFrames();

private:

    ///< TODO: frame rate
    const size_t _framerate{24};

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
        {Qt::Key_Left,      bindCmd(backward3frame)},   
        {Qt::Key_Right,     bindCmd(forward3frame)},       
    };
    // clang-format on

    ///< Timeline paused
    bool _paused{false};

    ///< Timeline running
    bool _running{true};

    ///< Inputs created
    std::vector<std::shared_ptr<IInput>> _inputs{};

    ///< Inputs that shoud be showed
    std::vector<size_t> _addedInputs{};

    ///< Stack containing the transformations to apply to the Inputs
    json::array_t _stack{};

    ///< Window to modify the video in real time
    std::unique_ptr<AppWindow> _app{nullptr};

    ///< Output File for the generation
    std::string _outputFile;
};
