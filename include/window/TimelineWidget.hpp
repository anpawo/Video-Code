/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** QtWindow
*/

#pragma once

#include <QPainter>
#include <QWidget>

class TimelineWidget : public QWidget
{
    Q_OBJECT
public:

    TimelineWidget(QWidget* parent, const size_t& index, const size_t& duration)
        : QWidget(parent), _index(index), _duration(duration)
    {
        setMinimumHeight(_height); // ensure timeline is visible
    }

protected:

    void paintEvent(QPaintEvent*) override
    {
        QPainter painter(this);
        painter.setRenderHint(QPainter::Antialiasing);

        // Background of the timeline
        painter.fillRect(rect(), QColor(0, 0, 0, 128)); // semitransparent black

        // Filled portion of the timeline
        if (_duration > 0) {
            double progress = double(_index + 1) / _duration;
            int barWidth = int(width() * progress);
            painter.fillRect(0, height() / 2 - _barHeight / 2, barWidth, _barHeight, Qt::red);
        }
    }

private:

    const size_t& _index;
    const size_t& _duration;

    const int _height{20};
    const int _barHeight{5};
};
