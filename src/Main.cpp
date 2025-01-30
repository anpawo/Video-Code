/*
** EPITECH PROJECT, 2024
** video-code
** File description:
** Main
*/

#include <opencv2/opencv.hpp>

#include "vm/LiveWindow.hpp"

int main(int argc, char *argv[])
{
    LiveWindow win(argc, argv, 1920, 1080);

    return win.run();
}
