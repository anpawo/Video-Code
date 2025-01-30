/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** WindowEvent
*/

#pragma once

#include <map>

#include "qevent.h"
#include "qwidget.h"

class WindowEvent : public QWidget {
public:

    WindowEvent(const std::map<int, std::function<void()>> &events, std::string &sourceFile, int width, int height, std::function<void()> &&mainLoop);
    ~WindowEvent() = default;

    void mainLoop();

protected:

    void keyPressEvent(QKeyEvent *event) override
    {
        auto e = _events.find(event->key());

        if (e != _events.end()) {
            e->second();
        }

        QWidget::keyPressEvent(event);
    }

private:

    std::function<void()> _mainLoop;

    const std::map<int, std::function<void()>> &_events;
};
