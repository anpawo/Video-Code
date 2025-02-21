/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** WindowEvent
*/

#include "vm/AppEvent.hpp"

AppEvent::AppEvent(const std::map<int, std::function<void()>> &events, const std::string &sourceFile, int width, int height, std::function<void()> &&mainLoop)
    : _mainLoop(mainLoop)
    , _events(events)
{
    ///< Define the settings of the window
    setStyleSheet("background-color: black;");
    setWindowTitle(("Video-Code  |  " + sourceFile).c_str());
    move(width / 2, 0);
    resize(width / 2, height / 2);
    show();
}

void AppEvent::mainLoop()
{
    _mainLoop();
}
