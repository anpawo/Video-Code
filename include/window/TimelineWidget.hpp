/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** QtWindow
*/

#pragma once

#include <qnamespace.h>
#include <stddef.h>

#include <QPainter>
#include <QWidget>
#include <format>

class TimelineWidget : public QWidget
{
    Q_OBJECT
public:

    TimelineWidget(QWidget* parent, const size_t& index, const size_t& duration, size_t width)
        : QWidget(parent), _index(index), _duration(duration), _width(width)
    {
        setMinimumHeight(_height);
        setMinimumWidth(_width);

        setAttribute(Qt::WA_TranslucentBackground);
        setAutoFillBackground(false);
    }

protected:

    void paintEvent(QPaintEvent*) override
    {
        QPainter painter(this);
        painter.setRenderHint(QPainter::Antialiasing);

        // Background of the timeline
        painter.fillRect(rect(), Qt::transparent); // semitransparent black

        // Filled portion of the timeline
        if (_duration > 0) {

            ///< Gray bar
            double grayBarRadius = _barHeight / 2.0;
            int gray = 204;
            int opacity = 96;

            QRectF grayBarRect(
                _offsetX,
                height() / 3.0 - _barHeight / 2.0,
                width() - (_offsetX * 2),
                _barHeight
            );

            painter.setBrush(QColor(gray, gray, gray, opacity));
            painter.setPen(Qt::NoPen); // no border
            painter.drawRoundedRect(grayBarRect, grayBarRadius, grayBarRadius);

            ///< Red bar
            double redBarRadius = _barHeight / 2.0;
            double progress = double(_index + 1) / (_duration);
            double barWidth = (width() - (_offsetX * 2)) * progress;

            QRectF redBarRect(
                _offsetX,
                height() / 3.0 - _barHeight / 2.0,
                barWidth,
                _barHeight
            );

            painter.setBrush(Qt::red);
            painter.setPen(Qt::NoPen); // no border
            painter.drawRoundedRect(redBarRect, redBarRadius, redBarRadius);

            ///< Index / NbFrame / Gray Rect Bg
            // Set font first
            QFont font;
            font.setPointSize(15);
            painter.setFont(font);
            painter.setPen(Qt::white);

            // Prepare the text
            QString text = QString::fromStdString(std::format("{} / {}", _index + 1, _duration));
            QFontMetrics fm(painter.font());
            QSizeF textSize = fm.size(Qt::TextSingleLine, text);

            // Calculate rectangle with some padding
            const int paddingX = 12; // horizontal padding
            const int paddingY = 6;  // vertical padding

            qreal rectWidth = textSize.width() + 2 * paddingX;
            qreal rectHeight = textSize.height() + 2 * paddingY;

            // Centered rectangle
            qreal rectX = (width() - rectWidth) / 2.0;
            qreal rectY = height() - rectHeight - 10; // 10px above bottom

            // Draw rounded gray background
            QRectF grayRect(rectX, rectY, rectWidth, rectHeight);
            double radius = rectHeight / 2.0; // pill shape
            gray = 96;
            painter.setBrush(QColor(gray, gray, gray, opacity));
            painter.setPen(Qt::NoPen);
            painter.drawRoundedRect(grayRect, radius, radius);

            // Draw text centered inside the rectangle
            painter.setPen(Qt::white);
            painter.drawText(grayRect, Qt::AlignCenter, text);
        }
    }

private:

    const size_t& _index;
    const size_t& _duration;

    ///< Widget Size
    const int _width;
    const int _height{75};

    ///< Bar
    const int _barHeight{5};
    const int _offsetX{50};
};
