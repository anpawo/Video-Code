/*
** EPITECH PROJECT, 2026
** video-code
** File description:
** Config
*/

#pragma once

#include <string>

struct Config
{
    float screenWidth = 1920.f;
    float screenHeight = 1080.f;

    float windowRatio = 0.5f;

    float windowWidth = screenWidth * windowRatio;
    float windowHeight = screenHeight * windowRatio;

    int framerate;

    ///< Source & Output file
    std::string sourceFile;
    std::string outputFile;
};
