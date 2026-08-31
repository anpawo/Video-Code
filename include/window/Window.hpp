/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Window
*/

#pragma once

#include <QKeyEvent>
#include <QMainWindow>
#include <QTimer>
#include <chrono>
#include <vector>

#include "core/Core.hpp"
#include "vulkan/Mesh.hpp"
#include "window/TimelineWidget.hpp"
#include "window/VulkanWidget.hpp"

class QLabel;

// argparse is a COMMAND-LINE parser, and it was reaching five headers through
// this one — 1381 of the 1754 include events of a 75-line ScreenSize.cpp. Every
// use here is by reference, so a forward declaration is all a header needs; the
// definition belongs to the .cpp files that actually read a flag.
namespace argparse
{
    class ArgumentParser;
}

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

        ///< Config (Window / Framerate / Paths)
        Config config;

        ///< Core handling the images
        Core _core;

        ///< Timer for timeline updates
        QTimer* _timer;

        ///< Vulkan rendering surface (central widget)
        VulkanWidget* _vulkanWidget;

        ///< Timeline overlay
        TimelineWidget* _timeline{nullptr};

        ///< Keyboard-shortcut help overlay (toggled by 'H')
        QLabel* _helpOverlay{nullptr};

        ///< Frame-rate throttle for the Vulkan frame callback
        std::chrono::steady_clock::time_point _lastFrameTime{};
        std::vector<Mesh>                     _lastMeshes;
    };

} // namespace VC
