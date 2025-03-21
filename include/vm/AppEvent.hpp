/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** WindowEvent
*/

#pragma once

#include <qevent.h>
#include <qlabel.h>
#include <qwidget.h>

#include <map>

class AppEvent : public QWidget
{
public:

    AppEvent(const std::map<int, std::function<void()>> &events, const std::string &sourceFile, int width, int height, std::function<void()> &&mainLoop);
    ~AppEvent() = default;

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
