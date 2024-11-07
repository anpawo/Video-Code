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
    CommandFactory f{};

    f.addInputs(
        Input("video/v.mp4").as("mp4"),
        Input("video/v.mkv").as("mkv")
    );

    f.addFilters(
        Concatenate("mp4", "mkv", "va"),
        Concatenate("mp4", "mkv", "vb"),
        Concatenate("va", "vb", "vc"),
        Select("vc", "frame").set(2)
    );

    std::cout << f.generateCommand("output.png") << std::endl;
    f.generateOutput("output.png");

    return 0;
}
