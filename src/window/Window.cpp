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
    ///< Animation is advanced inside the Vulkan render loop via setFrameCallback(),
    ///< so no separate QTimer is needed. _timer is kept as nullptr.
    _timer = nullptr;

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

    ///< Wire up the frame callback before init so the first render already
    ///< has access to the animation state.
    ///< The callback throttles animation advancement to config.framerate fps so
    ///< that Vulkan rendering at display refresh rate doesn't consume frames too fast.
    const auto frameDuration = std::chrono::duration<double>(1.0 / config.framerate);
    _vulkanWidget->setFrameCallback([this, frameDuration]() -> std::vector<Mesh> {
        auto now = std::chrono::steady_clock::now();
        if (_lastMeshes.empty() || (now - _lastFrameTime) >= frameDuration) {
            _lastFrameTime = now;
            _lastMeshes = _core.generateMeshes();
        }
        return _lastMeshes;
    });

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
