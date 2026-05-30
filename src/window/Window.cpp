/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Window
*/

#include "window/Window.hpp"
#include "utils/Logger.hpp"

#include <QGuiApplication>
#include <QScreen>
#include <QStatusBar>
#include <algorithm>
#include <chrono>
#include <format>
#include <iostream>

// Window startup timer — measures wall time from the first line of the
// constructor until Vulkan init completes.  Printed once at startup.
static auto s_windowStart = std::chrono::high_resolution_clock::now();

VC::Window::Window(const argparse::ArgumentParser& parser, QWidget* parent)
    : QMainWindow(parent)
    , config({
          .screenWidth = parser.get<float>("--width"),
          .screenHeight = parser.get<float>("--height"),
          .windowRatio = parser.get<float>("--windowRatio"),

          .framerate = parser.get<int>("--framerate"),

          .sourceFile = parser.get("--file"),
          .outputFile = parser.get("--generate"),
      })
    , _core(parser, config)       // ← reloadSourceFile() runs here (Python + executeStack)
{
    using Clock = std::chrono::high_resolution_clock;
    using Ms    = std::chrono::duration<double, std::milli>;
    [[maybe_unused]] double core_ms = std::chrono::duration_cast<Ms>(Clock::now() - s_windowStart).count();
    VC_SLOG(std::format("[startup] Core ctor (Python load + executeStack): {:.1f}ms\n", core_ms));
    ///< Animation is advanced inside the Vulkan render loop via setFrameCallback(),
    ///< so no separate QTimer is needed. _timer is kept as nullptr.
    _timer = nullptr;

    ///< Vulkan central widget
    _vulkanWidget = new VulkanWidget(this);
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

    // Never create a status bar — calling statusBar()->hide() still allocates it
    // and reserves layout space, shrinking the VulkanWidget by ~22 px and making
    // the swapchain extent a non-multiple of the video resolution.

    // Pin the central widget to exactly windowWidth × windowHeight so the Vulkan
    // surface (and swapchain) is a clean multiple of the video resolution.
    QRect screen = QGuiApplication::primaryScreen()->availableGeometry();
    float scale = std::min(
        (float)screen.width() / config.windowWidth,
        (float)screen.height() / config.windowHeight
    );
    scale = std::min(scale, 1.0f);
    int w = (int)(config.windowWidth * scale);
    int h = (int)(config.windowHeight * scale);
    _vulkanWidget->setFixedSize(w, h);
    adjustSize();
    move(screen.center().x() - width() / 2, 0);
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
    QTimer::singleShot(0, _vulkanWidget, [this] {
        using Clock = std::chrono::high_resolution_clock;
        using Ms    = std::chrono::duration<double, std::milli>;
        // VulkanWidget::init() already prints per-step timing itself.
        _vulkanWidget->init();
        auto _t_tex = Clock::now();
        _core.uploadTextures(_vulkanWidget);
        [[maybe_unused]] double tex_ms   = std::chrono::duration_cast<Ms>(Clock::now() - _t_tex).count();
        [[maybe_unused]] double total_ms = std::chrono::duration_cast<Ms>(Clock::now() - s_windowStart).count();
        VC_SLOG(std::format("[startup] {:35s} {:7.1f}ms\n", "uploadTextures (CPU→GPU)", tex_ms));
        VC_SLOG(std::format("[startup] === total Window ctor → first-frame-ready: {:.1f}ms ===\n",
                                 total_ms));
    });
}

VC::Window::~Window() = default;

void VC::Window::keyPressEvent(QKeyEvent* event)
{
    if (event->key() == Qt::Key_Escape) {
        close();
    } else if (event->key() == Qt::Key_Space) {
        _core.pause();
    } else if (event->key() == Qt::Key_Down) {
        if (event->modifiers() & Qt::ControlModifier) {
            _core.goToPrevTimestamp();
        } else {
            _core.goToFirstFrame();
        }
    } else if (event->key() == Qt::Key_Up) {
        if (event->modifiers() & Qt::ControlModifier) {
            _core.goToNextTimestamp();
        } else {
            _core.goToLastFrame();
        }
    } else if (event->key() == Qt::Key_Left) {
        _core.backwardFrame(event->modifiers() & Qt::ControlModifier ? 5 : 1);
    } else if (event->key() == Qt::Key_Right) {
        _core.forwardFrame(event->modifiers() & Qt::ControlModifier ? 5 : 1);
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
