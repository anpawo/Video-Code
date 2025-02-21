/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** AppWindow
*/

#pragma once

#include "qapplication.h"
#include "qboxlayout.h"
#include "qlabel.h"
#include "qtimer.h"
#include "vm/AppEvent.hpp"

class AppWindow
{
public:

    AppWindow(int argc, char **argv, const std::map<int, std::function<void()>> &events, const std::string &sourceFile, int width, int height, int frameRate, std::function<void(QLabel &imageLabel)> &&mainLoop);

    ///< Start the app
    int run();

private:

    ///< QT app
    QApplication _app;

    ///< QT window
    AppEvent _window;

    ///< Label containing the image
    QLabel _imageLabel;

    ///< Layout linking the label and the window
    QVBoxLayout _imageLayout;

    ///< Encapsulation of the Main loop which updates the current frame
    QTimer _timer;

    ///< Main loop
    std::function<void(QLabel &imageLabel)> _mainLoop;
};
