/*
** EPITECH PROJECT, 2024
** video-code
** File description:
** Main
*/

#include <argparse/argparse.hpp>
#include <opencv2/opencv.hpp>

#include "vm/VideoCode.hpp"

int main(int argc, char *argv[])
{
    argparse::ArgumentParser parser("Video-Code", "", argparse::default_arguments::help);

    parser.add_argument("--sourceFile").default_value("video.py").help("file containing the steps to create the video.");
    parser.add_argument("--generate").nargs(0, 1).default_value("output.mov").help("generate the video.");
    parser.parse_args(argc, argv);

    VideoCode vc(argc, argv, 1920, 1080, parser.get("--sourceFile"), parser.is_used("--generate"), parser.get<std::string>("--generate"));

    return vc.run();
}
