/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** QtWindow
*/

#pragma once

#include <QBoxLayout>
#include <QImage>
#include <QKeyEvent>
#include <QLabel>
#include <QMainWindow>
#include <QTimer>
#include <argparse/argparse.hpp>
#include <opencv2/opencv.hpp>

#include "TimelineWidget.hpp"
#include "core/Core.hpp"

namespace VC
{
    class Window : public QMainWindow
    {
        Q_OBJECT

    public:

        Window(const argparse::ArgumentParser& parser, QWidget* parent = nullptr);
        ~Window() override;

        void mainRoutine();

    protected:

        void keyPressEvent(QKeyEvent* event) override;

    private:

        ///< Window size
        const size_t _width;
        const size_t _height;

        ///< Framerate of the video
        const size_t _framerate;

        ///< Core handling the images
        Core _core;

        ///< Timer handling the Routine
        QTimer* _timer;

        ///< Image Label
        QLabel* _imageLabel;
        ///< Image Layout
        QVBoxLayout* _imageLayout;
        ///< Widget containing the layout
        QWidget* _centralWidget;

        ///< Timeline Widget
        TimelineWidget* _timeline;
    };
};
