/*
** EPITECH PROJECT, 2024
** video-code
** File description:
** Main
*/

#include <QApplication>
#include <QPushButton>
#include <QVBoxLayout>
#include <QWidget>
#include <opencv2/opencv.hpp>

// #include "vm/LiveWindow.hpp"

int main(int argc, char *argv[])
{
    // LiveWindow win(1920, 1080);

    // win.run();

    QApplication app(argc, argv);

    // Create the main window
    QWidget window;
    window.setWindowTitle("Simple Qt6 App");

    // Create a button
    QPushButton button("Click Me", &window);
    QObject::connect(&button, &QPushButton::clicked, &app, &QApplication::quit);

    // Layout setup
    QVBoxLayout layout;
    layout.addWidget(&button);
    window.setLayout(&layout);

    window.resize(300, 200);
    window.show();

    return app.exec();
}
