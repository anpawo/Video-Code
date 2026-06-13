/*
** EPITECH PROJECT, 2024
** video-code
** File description:
** Main
*/

#include <pybind11/embed.h>

#include <QApplication>
#include <QMainWindow>
#include <QMessageLogContext>
#include <argparse/argparse.hpp>
#include <cstdlib>
#include <nlohmann/json.hpp>
#include <opencv2/core/utils/logger.hpp>
#include <opencv2/opencv.hpp>

#include "compiler/Compiler.hpp"
#include "test/VisualTest.hpp"
#include "window/Window.hpp"

namespace py = pybind11;

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
        .default_value(1920.f)
        .scan<'f', float>();

    p
        .add_argument("--height")
        .default_value(1080.f)
        .scan<'f', float>();

    p
        .add_argument("--windowRatio")
        .default_value(0.5f)
        .scan<'f', float>()
        .help("Ratio of preview window compared to the video size.");

    p
        .add_argument("--framerate")
        .default_value(30)
        .scan<'i', int>()
        .help("Output video framerate (fps). Scenes are authored at 30fps regardless "
              "of this value — frames are duplicated or dropped to resample to it.");

    p
        .add_argument("--showstack")
        .flag()
        .help("Show the steps of the video while being generated.");

    p
        .add_argument("--showtimeline")
        .flag()
        .help("Show the timeline of the video.");

    p
        .add_argument("--visual-test")
        .flag()
        .help("Run the visual regression suite (golden-frame + hot-reload equivalence checks) and exit.");

    p
        .add_argument("--update-golden")
        .flag()
        .help("With --visual-test, (re)write the golden images instead of comparing against them.");

    p
        .add_argument("--hwencode")
        .flag()
        .help("Encode with the hardware H.264 encoder (h264_videotoolbox) instead of libx264. Faster and lighter on CPU, but quality/bitrate behavior differs from CRF.");
}

int main(int argc, char *argv[])
{
    // Initialize the Python interpreter once for the whole process.
    // false = don't override Qt's signal handlers.
    py::scoped_interpreter guard{false};
    py::exec("import sys; sys.path.insert(0, '')");

    // Suppress the spurious Qt/macOS fullscreen position warning
    // Message: "qt.qpa.window: Window position QRect(-1,0 1470x826) outside any known screen, using primary screen"
    qInstallMessageHandler([](QtMsgType type, const QMessageLogContext &, const QString &msg) {
        if (type == QtWarningMsg && msg.contains("outside any known screen"))
            return;
        fprintf(stderr, "%s\n", msg.toLocal8Bit().constData());
    });

    // Hide OpenCV logs
    cv::utils::logging::setLogLevel(cv::utils::logging::LOG_LEVEL_SILENT);

    // Parse the arguments
    argparse::ArgumentParser parser(
        "./videocode",
        "A video editing software made by Marius Rousset and Hippolyte Lefer.",
        argparse::default_arguments::help
    );
    setParserArgument(parser);
    try {
        parser.parse_args(argc, argv);
    } catch (const std::exception &e) {
        std::cerr << e.what() << std::endl;
        return EXIT_FAILURE;
    }

    // Visual regression suite (headless — no window, no Qt event loop)
    if (parser.get<bool>("--visual-test")) {
        VC::VisualTest visualTest(parser);
        return visualTest.run(parser.get<bool>("--update-golden"));
    }

    // Generate the video (headless — no window, no Qt event loop)
    if (parser.is_used("--generate")) {
        VC::Compiler compiler(parser);
        return compiler.generateVideo();
    }

    // Preview/Edit the video
    QApplication app(argc, argv);
    VC::Window   window(parser);
    return app.exec();
}

// binding python / cpp

// boucle sens prediction video martin baldinger
