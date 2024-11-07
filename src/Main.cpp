/*
** EPITECH PROJECT, 2024
** video-code
** File description:
** Main
*/

#include <iostream>

#include "CommandFactory.hpp"
#include "Filter/Concatenate.hpp"
#include "Filter/Overlay.hpp"
#include "Filter/Select.hpp"

// Example
// ffmpeg -i input1.mp4 -i input2.mp4 -filter_complex '[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[v][a]' -map '[v]' -map '[a]' output.mp4

int main()
{
    CommandFactory f{};

    f.addInputs(
        Input("video/v.mp4").as("mp4"),
        Input("video/v.mkv").as("mkv"),
        Input("video/ECS.png").as("img")
    );

    f.addFilters(
        Concatenate("mp4", "mkv", "va"),
        Concatenate("mp4", "mkv", "vb"),
        Concatenate("va", "vb", "vc"),
        Overlay("vc", "img", "vd").set(100, 100),
        Select("vd", "frame").set(2)
    );

    std::cout << f.generateCommand("output.mp4") << std::endl;
    f.generateOutput("output.png");

    return 0;
}
