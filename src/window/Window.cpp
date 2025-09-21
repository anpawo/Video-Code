/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Window
*/

#include "window/Window.hpp"

#include "qnamespace.h"

VC::Window::Window(const argparse::ArgumentParser& parser, QWidget* parent)
    : QMainWindow(parent)
    , _width(parser.get<int>("--width"))
    , _height(parser.get<int>("--height"))
    , _framerate(parser.get<int>("--framerate"))
    , _core(parser)
{
    ///< Routine settings
    _timer = new QTimer(this);
    connect(_timer, &QTimer::timeout, this, &Window::mainRoutine);
    _timer->start(1000 / _framerate);

    ///< Setup the layout and image
    _imageLabel = new QLabel(this);
    _imageLayout = new QVBoxLayout();
    _imageLayout->setContentsMargins(0, 0, 0, 0);
    _imageLayout->addWidget(_imageLabel);
    _centralWidget = new QWidget(this);
    _centralWidget->setLayout(_imageLayout);
    setCentralWidget(_centralWidget);

    ///< Window settings
    setStyleSheet("background-color: black;");
    setWindowTitle(("Video-Code  |  " + parser.get("--sourceFile")).c_str());
    move(_width / 2, 0);
    resize(_width / 2, _height / 2);
    show();
}

VC::Window::~Window() = default;

void VC::Window::keyPressEvent(QKeyEvent* event)
{
    if (event->key() == Qt::Key_Escape) {
        close();
    } else if (event->key() == Qt::Key_Space) {
        _core.pause();
    } else if (event->key() == Qt::Key_Down) {
        _core.goToFirstFrame();
    } else if (event->key() == Qt::Key_Up) {
        _core.goToLastFrame();
    } else if (event->key() == Qt::Key_Left) {
        _core.backward3frames();
    } else if (event->key() == Qt::Key_Right) {
        _core.forward3frames();
    } else {
        QMainWindow::keyPressEvent(event);
    }
}

void VC::Window::mainRoutine()
{
    _core.updateFrame(*_imageLabel);
}
