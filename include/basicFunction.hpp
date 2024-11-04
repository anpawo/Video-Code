/*
** EPITECH PROJECT, 2024
** video-code
** File description:
** understanding
*/

#pragma once

#include <string>

/**
 * @brief concatenates 2 videos. the second video will be starting at the end of the first video.

 * @param v1 first video
 * @param v2 second video
 * @param output name of the output video
 */
void concatenateVideo(std::string v1, std::string v2, std::string output = "output.mp4");

/**
 * @brief overlays one video on another. @param overlay will be on the @param main video.

 * @param main first video
 * @param overlay second video
 * @param output name of the output video
 */
void overlayVideo(std::string main, std::string overlay, std::string output = "output.mp4");
