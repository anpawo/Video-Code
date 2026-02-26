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
#include <opencv2/core/utils/logger.hpp>
#include <opencv2/opencv.hpp>
#include <iostream>

#include "compiler/Compiler.hpp"
#include "window/Window.hpp"

void setParserArgument(argparse::ArgumentParser &p)
{
    p
        .add_argument("--file")
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

    p
        .add_argument("--showstack")
        .flag()
        .help("Show the steps of the video while being generated.");

    p
        .add_argument("--showtimeline")
        .flag()
        .help("Show the timeline of the video.");

    p
        .add_argument("--ui")
        .flag()
        .help("Launch UI mode (dynamic editor).");

    p
        .add_argument("--ui-schema")
        .flag()
        .help("Print UI schema (inputs/effects) for the dynamic editor.");
}

static int printUiSchema()
{
    const std::string command = "python3 videocode/ui_schema.py";

    FILE* pipe = popen(command.c_str(), "r");
    if (!pipe) {
        std::cerr << "VideoCode: Failed to run UI schema generator." << std::endl;
        return 1;
    }

    char buffer[4096];
    while (fgets(buffer, sizeof(buffer), pipe) != nullptr) {
        std::cout << buffer;
    }

    int status = pclose(pipe);
    return status == 0 ? 0 : 1;
}

int main(int argc, char *argv[])
{
    // Hide OpenCV logs
    cv::utils::logging::setLogLevel(cv::utils::logging::LOG_LEVEL_SILENT);

    argparse::ArgumentParser parser(
        "./videocode",
        "A video editing software made by Marius Rousset and Hippolyte Lefer.",
        argparse::default_arguments::help
    );

    setParserArgument(parser);
    parser.parse_args(argc, argv);

    if (parser.get<bool>("--ui-schema")) {
        return printUiSchema();
    }

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
