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

    ///< Output video framerate (fps) — independent of SCENE_FRAMERATE. The
    ///< Compiler resamples (duplicates/drops) scene frames to reach this rate.
    int framerate;

    ///< Framerate that scene-side frame indices/durations are expressed in —
    ///< matches videocode/constants.py FRAMERATE. Fixed: scenes are authored
    ///< in this unit regardless of the output framerate.
    static constexpr int SCENE_FRAMERATE = 30;

    ///< Use the hardware H.264 encoder (h264_videotoolbox) instead of libx264.
    bool hwEncode = false;

    ///< Source & Output file
    std::string sourceFile;
    std::string outputFile;
};
