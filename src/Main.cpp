/*
** EPITECH PROJECT, 2024
** video-code
** File description:
** Main
*/

#include <opencv2/opencv.hpp>

#include "vm/LiveWindow.hpp"

int main()
{
    LiveWindow win(1920, 1080);

    win.run();
}
