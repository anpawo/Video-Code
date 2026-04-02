/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Window
*/

#include "window/Window.hpp"

VC::Window::Window(const argparse::ArgumentParser& parser, QWidget* parent)
    : QMainWindow(parent)
    , config({
          .screenWidth = parser.get<float>("--width"),
          .screenHeight = parser.get<float>("--height"),

          .framerate = parser.get<int>("--framerate"),

          .sourceFile = parser.get("--file"),
          .outputFile = parser.get("--generate"),
      })
    , _core(parser, config)
{
    ///< Timer for timeline updates (Vulkan drives its own render loop via update())
    _timer = new QTimer(this);
    connect(_timer, &QTimer::timeout, this, &Window::mainRoutine);
    _timer->start(1000 / config.framerate);

    ///< Vulkan central widget
    _vulkanWidget = new VulkanWidget(this);
    _vulkanWidget->setFixedSize(config.windowWidth, config.windowHeight);
    setCentralWidget(_vulkanWidget);

    /// TODO: fix the timeline
    ///< Timeline overlay (child of the Vulkan widget so it sits on top)
    // if (_core._showtimeline) {
    //     _timeline = new TimelineWidget(_vulkanWidget, _core._index, _core._nbFrame, _width / 2);
    //     _timeline->setGeometry(
    //         0,
    //         _vulkanWidget->height() - _timeline->minimumHeight(),
    //         _timeline->minimumWidth(),
    //         _timeline->minimumHeight()
    //     );
    //     _timeline->raise();
    // }

    /// TODO: function for that
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

    // Resize the QT window and move it to the top-right corner
    move(config.windowWidth, 0);
    resize(config.windowWidth, config.windowHeight);
    show();

    ///< Defer Vulkan init until the event loop is running and the native
    ///< window handle is guaranteed to be available.
    QTimer::singleShot(0, _vulkanWidget, [this] { _vulkanWidget->init(); });
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
}

void VC::Window::mainRoutine()
{
    auto meshes = _core.generateMeshes();
    _vulkanWidget->setMeshes(meshes);
    if (_timeline) {
        _timeline->update();
    }
}
