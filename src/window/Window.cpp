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

    ///< Window name centered
    std::string l = "video-code";
    std::string sep = "  |  ";
    std::string r = parser.get("--file");
    if (l.size() < r.size()) {
        l = std::string(r.size() - l.size(), ' ') + l;
    } else if (l.size() > r.size()) {
        r = r + std::string(l.size() - r.size(), ' ');
    }
    setWindowTitle((l + sep + r).c_str());

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
        _core.backward1frame();
    } else if (event->key() == Qt::Key_Right) {
        _core.forward1frame();
    } else {
        QMainWindow::keyPressEvent(event);
    }
    _core.updateFrame(*_imageLabel);
}

void VC::Window::mainRoutine()
{
    _core.updateFrame(*_imageLabel);
}
