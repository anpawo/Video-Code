/*
** EPITECH PROJECT, 2024
** video-code
** File description:
** Main
*/

#include <QApplication>
#include <QMainWindow>
#include <argparse/argparse.hpp>
#include <nlohmann/json.hpp>
#include <opencv2/opencv.hpp>

#include "compiler/Compiler.hpp"
#include "window/Window.hpp"

void setParserArgument(argparse::ArgumentParser &p)
{
    p
        .add_argument("--sourceFile")
        .default_value("video.py")
        .help("File containing the code to generate the video.");

    p
        .add_argument("--generate")
        .nargs(0, 1)
        .default_value("output.mp4")
        .help("Generate the video, otherwise the program runs in edit mode where you can visualize the video as you write it.");

    p
        .add_argument("--width")
        .default_value(1920)
        .scan<'i', int>();

    p
        .add_argument("--height")
        .default_value(1080)
        .scan<'i', int>();

    p
        .add_argument("--framerate")
        .default_value(30)
        .scan<'i', int>();
}

int main(int argc, char *argv[])
{
    argparse::ArgumentParser parser(
        "./videocode",
        "A video editing software made by Marius Rousset and Hippolyte Lefer.",
        argparse::default_arguments::help
    );

    setParserArgument(parser);
    parser.parse_args(argc, argv);

    if (parser.is_used("--generate")) {
        // Compile Mode
        VC::Compiler compiler(parser);

        return compiler.generateVideo();

    } else {
        // Edit Mode
        QApplication app(argc, argv);

        VC::Window window(parser);

        return app.exec();
    }
}

// binding python / cpp

// boucle sens prediction video martin baldinger
