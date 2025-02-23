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
    argparse::ArgumentParser parser("./videocode", "", argparse::default_arguments::help);

    parser.add_argument("--sourceFile")
        .default_value("video.py")
        .help("file containing the steps to create the video.");
    parser.add_argument("--generate")
        .nargs(0, 1)
        .default_value("output.mp4")
        .help("generate the video. without this flag, the program runs in edit mode where you can visualize the video as you write it.");

    parser.parse_args(argc, argv);

    VideoCode vc(argc, argv, 1920, 1080, parser.get("--sourceFile"), parser.is_used("--generate"), parser.get<std::string>("--generate"));

    return vc.run();
}
