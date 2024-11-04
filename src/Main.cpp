/*
** EPITECH PROJECT, 2024
** video-code
** File description:
** Main
*/

#include <iostream>

#include "CommandFactory.hpp"
#include "Filter/Concatenate.hpp"

// Example
// ffmpeg -i input1.mp4 -i input2.mp4 -filter_complex '[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[v][a]' -map '[v]' -map '[a]' output.mp4

int main()
{
    // concatenateVideo("video/v.mp4", "video/v.mp4");
    // overlayVideo("video/v.mp4", "video/v.mp4");

    CommandFactory f{};

    f.addInput(
        "lol",
        "haha"
    );

    std::cout << f._filters.size() << std::endl;
    f.addFilter(
        Concatenate(),
        Concatenate(),
        Concatenate()
    );
    std::cout << f._filters.size() << std::endl;
    f.addFilter(
        Concatenate(),
        Concatenate(),
        Concatenate()
    );
    std::cout << f._filters.size() << std::endl;
    std::cout << f._filters[0]->getCommand() << std::endl;
    std::cout << f._filters[2]->getCommand() << std::endl;

    return 0;
}
