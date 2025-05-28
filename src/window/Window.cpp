/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Window
*/

#include "window/Window.hpp"

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
    _timer->start(_framerate);

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
    } else {
        QMainWindow::keyPressEvent(event);
    }
}

void VC::Window::mainRoutine()
{
    _core.updateFrame(*_imageLabel);
}

// void VideoCode::pause()
// {
//     _paused = !_paused;
//     std::cout << std::format("Timeline {} at frame '{}'.", _paused ? "paused" : "unpaused", _index) << std::endl;
// }

// void VideoCode::stop()
// {
//     _running = false;
//     QApplication::quit();
// }

// void VideoCode::goToFirstFrame()
// {
//     _index = 0;
//     std::cout << std::format("Jumped backward to the first frame of the video: {}", _index) << std::endl;
// }

// void VideoCode::goToLastFrame()
// {
//     if (_frames.size()) {
//         _index = _frames.size() - 1;
//     }
//     std::cout << std::format("Jumped forward to the last frame of the video: {}", _index) << std::endl;
// }

// void VideoCode::backward3frame()
// {
//     if (_index < 3 * _framerate) {
//         _index = 0;
//     } else {
//         _index -= 3 * _framerate;
//     }
// }

// void VideoCode::forward3frame()
// {
//     _index += 3 * _framerate;
//     if (_index > _frames.size()) {
//         _index = _frames.size() - 1;
//     }
// }
