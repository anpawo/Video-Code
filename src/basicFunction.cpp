/*
** EPITECH PROJECT, 2024
** video-code
** File description:
** understanding
*/

#include "basicFunction.hpp"

#include <stdlib.h>

#include <cstdlib>

void concatenateVideo(std::string first, std::string second, std::string output)
{
    // clang-format off
    std::string cmd = 
        "ffmpeg -i " + first + " -i " + second +   ///> input files


                                            ///> -filter_complex is a complex filter, it takes many inputs and/or outputs

                                            ///> [0:v] refers to the video stream of the first input ("v1", index 0)
                                            ///> [0:a] refers to the audio stream of the first input ("v1", index 0)
                                            ///> [1:v] refers to the video stream of the second input ("v2", index 1)
                                            ///> [1:a] refers to the audio stream of the second input ("v2", index 1)

                                            ///> concat defines the complex filter

                                            ///> n=2 specifies the number of inputs, 2
                                            ///> v=1 indicates there is one video stream in the output
                                            ///> a=1 indicates there is one audio stream in the output

                                            ///> output specify the output filename
        " -filter_complex '[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[v][a]' -map '[v]' -map '[a]' " + output;
    // clang-format on
    system(cmd.c_str());
}

void overlayVideo(std::string main, std::string overlay, std::string output)
{
    std::string cmd = "ffmpeg -i " + main + " -i " + overlay + " -filter_complex '[0:v][1:v]overlay=100:100[v]' -map '[v]' -map 0:a " + output;
    system(cmd.c_str());
}
