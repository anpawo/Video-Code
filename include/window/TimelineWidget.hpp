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

            int redBarHeight = _barHeight + 1;

            ///< Gray bar
            int grayBarHeight = redBarHeight;
            double grayBarRadius = grayBarHeight / 2.0;
            int gray = 170;
            int opacity = 120;
            int shadowOpacity = 70;
            int shadowOffsetY = 3;
            int textBgGray = 0;
            int textBgOpacity = shadowOpacity + 30;

            QRectF grayBarRect(
                _offsetX,
                height() / 3.0 - grayBarHeight / 2.0,
                width() - (_offsetX * 2),
                grayBarHeight
            );

            QRectF grayShadowRect(
                grayBarRect.x(),
                grayBarRect.y() + shadowOffsetY + (grayBarHeight * 0.25),
                grayBarRect.width(),
                grayBarHeight * 0.5
            );

            painter.setBrush(QColor(0, 0, 0, shadowOpacity));
            painter.setPen(Qt::NoPen);
            painter.drawRoundedRect(grayShadowRect, grayBarRadius, grayBarRadius);

            painter.setBrush(QColor(gray, gray, gray, opacity));
            painter.setPen(Qt::NoPen); // no border
            painter.drawRoundedRect(grayBarRect, grayBarRadius, grayBarRadius);

            ///< Red bar
            double redBarRadius = redBarHeight / 2.0;
            double progress = double(_index + 1) / (_duration);
            double barWidth = (width() - (_offsetX * 2)) * progress;

            QRectF redBarRect(
                _offsetX,
                height() / 3.0 - redBarHeight / 2.0,
                barWidth,
                redBarHeight
            );

            QRectF redShadowRect(
                redBarRect.x(),
                redBarRect.y() + shadowOffsetY + (redBarHeight * 0.25),
                redBarRect.width(),
                redBarHeight * 0.5
            );

            painter.setBrush(QColor(0, 0, 0, shadowOpacity));
            painter.setPen(Qt::NoPen);
            painter.drawRoundedRect(redShadowRect, redBarRadius, redBarRadius);

            QRectF redGlowRect(
                redBarRect.x(),
                redBarRect.y(),
                redBarRect.width(),
                redBarRect.height()
            );

            painter.setBrush(QColor(255, 0, 0, 40));
            painter.setPen(Qt::NoPen);
            painter.drawRoundedRect(redGlowRect, redBarRadius, redBarRadius);

            QLinearGradient redGradient(redBarRect.topLeft(), redBarRect.bottomLeft());
            redGradient.setColorAt(0.0, QColor(255, 80, 80));
            redGradient.setColorAt(1.0, QColor(200, 0, 0));
            painter.setBrush(redGradient);
            painter.setPen(QPen(QColor(255, 255, 255, 80), 1)); // subtle outline
            painter.drawRoundedRect(redBarRect, redBarRadius, redBarRadius);

            ///< Red handle (playhead)
            double handleRadius = redBarHeight * 2.5;
            double handleX = _offsetX + barWidth;
            double handleY = height() / 3.0;
            QRectF handleRect(
                handleX - handleRadius / 2.0,
                handleY - handleRadius / 2.0,
                handleRadius,
                handleRadius
            );

            QRectF handleShadowRect(
                handleRect.x(),
                handleRect.y() + shadowOffsetY,
                handleRect.width(),
                handleRect.height()
            );

            painter.setBrush(QColor(0, 0, 0, shadowOpacity));
            painter.setPen(Qt::NoPen);
            painter.drawEllipse(handleShadowRect);

            QLinearGradient handleGradient(handleRect.topLeft(), handleRect.bottomLeft());
            handleGradient.setColorAt(0.0, QColor(255, 90, 90));
            handleGradient.setColorAt(1.0, QColor(200, 0, 0));
            painter.setBrush(handleGradient);
            painter.setPen(Qt::NoPen);
            painter.drawEllipse(handleRect);

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

            // Left aligned rectangle
            qreal rectX = _offsetX;
            qreal rectY = height() - rectHeight - 10; // 10px above bottom

            // Draw rounded gray background
            QRectF grayRect(rectX, rectY, rectWidth, rectHeight);
            double radius = rectHeight / 2.0; // pill shape
            painter.setBrush(QColor(textBgGray, textBgGray, textBgGray, textBgOpacity));
            painter.setPen(Qt::NoPen);
            painter.drawRoundedRect(grayRect, radius, radius);

            // Draw text centered inside the rectangle (no extra text shadow)
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
    const int _barHeight{3};
    const int _offsetX{24};
};
