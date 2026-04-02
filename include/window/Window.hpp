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
#include <argparse/argparse.hpp>

#include "core/Core.hpp"
#include "window/TimelineWidget.hpp"
#include "window/VulkanWidget.hpp"

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
    };

} // namespace VC
