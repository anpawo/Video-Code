/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** AppWindow
*/

#include "vm/AppWindow.hpp"

#include <qlabel.h>

AppWindow::AppWindow(int argc, char **argv, const std::map<int, std::function<void()>> &events, const std::string &sourceFile, int width, int height, int frameRate, std::function<void(QLabel &imageLabel)> &&mainLoop)
    : _app(argc, argv)
    , _window(events, sourceFile, width, height, [this]() { _mainLoop(_imageLabel); })
    , _mainLoop(mainLoop)
{
    ///< Setup the layouts and images
    _imageLayout.setContentsMargins(0, 0, 0, 0);
    _imageLayout.addWidget(&_imageLabel);
    _window.setLayout(&_imageLayout);

    ///< Connect the main loop with the window
    QObject::connect(&_timer, &QTimer::timeout, &_window, &AppEvent::mainLoop);
    _timer.start(frameRate);
}

int AppWindow::run()
{
    return _app.exec();
}
