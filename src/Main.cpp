/*
** EPITECH PROJECT, 2024
** video-code
** File description:
** Main
*/

#include <iostream>

#include "CommandFactory.hpp"
#include "Filter/Concatenate.hpp"
#include "Filter/Select.hpp"

// Example
// ffmpeg -i input1.mp4 -i input2.mp4 -filter_complex '[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[v][a]' -map '[v]' -map '[a]' output.mp4

int main()
{
    // First Try
    //      concatenateVideo("video/v.mp4", "video/v.mp4");
    //      overlayVideo("video/v.mp4", "video/v.mp4");

    // Second try
    CommandFactory f{};

    f.addInputs(
        "video/v.mp4",
        "video/v.mkv"
    );

    f.addFilters(
        // Concatenate("video/v.mp4", "video/v.mkv", "va"),
        // Concatenate("video/v.mp4", "video/v.mkv", "vb"),
        // Concatenate("va", "vb", "vc"),
        Select("video/v.mp4", "frame").set(2)
    );

    std::cout << f.generateCommand("output.png") << std::endl;
    // f.generateOutput("output.png");
    // f.generateVideo("output.mp4");
    // f.generateVideo("output.mkv");

    return 0;
}
