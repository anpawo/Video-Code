/*
** EPITECH PROJECT, 2024
** video-code
** File description:
** understanding
*/

#include "basicFunction.hpp"

#include <stdlib.h>

#include <cstdlib>

void concatenateVideo(std::string v1, std::string v2, std::string output)
{
    std::string cmd = "ffmpeg -i " + v1 + " -i " + v2 + " -filter_complex '[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[v][a]' -map '[v]' -map '[a]' " + output;
    system(cmd.c_str());
}
