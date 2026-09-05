/*
** EPITECH PROJECT, 2024
** video-code
** File description:
** Main
*/

#include <pybind11/embed.h>
#include <sys/socket.h>

#include <QApplication>
#include <QGuiApplication>
#include <QMainWindow>
#include <QMessageLogContext>
#include <QSocketNotifier>
#include <QTimer>
#include <argparse/argparse.hpp>
#include <csignal>
#include <cstdlib>
#include <fstream>
#include <nlohmann/json.hpp>
#include <opencv2/core/utils/logger.hpp>
#include <opencv2/opencv.hpp>

#include "compiler/Compiler.hpp"
#include "test/VisualTest.hpp"
#include "window/Editor.hpp"
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
        .add_argument("-w", "--width")
        .default_value(1920.f)
        .scan<'f', float>()
        .help("Output width in pixels. The only way to change it — a scene cannot.");

    p
        .add_argument("--height")
        .default_value(1080.f)
        .scan<'f', float>()
        .help("Output height in pixels. (No -h: argparse reserves it for --help.)");

    p
        .add_argument("--windowRatio")
        .default_value(0.5f)
        .scan<'f', float>()
        .help("Ratio of preview window compared to the video size.");

    p
        .add_argument("--framerate")
        .default_value(30)
        .scan<'i', int>()
        .help(
            "Output video framerate (fps). Scenes are authored at 30fps regardless "
            "of this value — frames are duplicated or dropped to resample to it."
        );

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
        .add_argument("--inspect")
        .flag()
        .help(
            "Run --file and print what it makes as JSON on stdout — the elements with their class, "
            "line, on-screen span and effects, the waits and the moments it named — then exit. "
            "The timeline as text, for a script or an agent that cannot see the window."
        );

    p
        .add_argument("--update-golden")
        .flag()
        .help("With --visual-test, (re)write the golden images instead of comparing against them.");

    p
        .add_argument("--editor")
        .flag()
        .help(
            "Open the editing shell (dock, timeline, properties, scene buffer) instead of the "
            "bare preview window. The chrome is QML read from disk, so it reloads when you save it."
        );

    p
        .add_argument("--check-chrome")
        .flag()
        .help(
            "Load the editor chrome, report whether it loaded, and exit — WITHOUT showing a "
            "window. macOS has no public API for choosing a window's Space, so a check that "
            "opens one lands on whichever desktop you are working on."
        );

    p
        .add_argument("--screenshot")
        .help(
            "With --editor, write the shell's first painted frame to this PNG and exit. The window "
            "grabs itself, so nothing floating above it ends up in the picture."
        );

    p
        .add_argument("--hwencode")
        .flag()
        .help("Encode with the hardware H.264 encoder (h264_videotoolbox) instead of libx264. Faster and lighter on CPU, but quality/bitrate behavior differs from CRF.");

    p
        .add_argument("--from")
        .help(
            "With --generate, render from this point: seconds (\"12.5\") or the name of a "
            "timestamp() in the scene. Sounds keep their place — one that began earlier is "
            "cut, not moved. Clamped to the scene."
        );

    p
        .add_argument("--to")
        .help("With --generate, stop at this point — seconds or a timestamp() name. Clamped to the scene.");

    p
        .add_argument("--sheet")
        .scan<'i', int>()
        .help(
            "With an image --generate, lay this many moments side by side in the one file, "
            "evenly spaced from --from to --to and each labelled with its time. One look shows the motion."
        );
}

namespace
{
    // ── ^C has to work ────────────────────────────────────────────────────
    // A Qt application run from a terminal ignored SIGINT entirely: Control-C
    // printed nothing, the window stayed, the shell never got its prompt back,
    // and the only way out was to hunt the pid. Worse, the signal did reach the
    // language server child — killing it — so the editor announced that pyright
    // "could not be started" and then carried on without it.
    //
    // A signal handler may not touch Qt: it interrupts the process anywhere,
    // including inside the event loop's own bookkeeping. So it does the one
    // thing POSIX promises is safe — a byte down a pipe — and a notifier turns
    // that byte into an ordinary quit on the event loop's own thread, which runs
    // every destructor and takes the child processes with it.
    int signalPipe[2] = {-1, -1};

    void onSignal(int)
    {
        const char                     byte = 1;
        [[maybe_unused]] const ssize_t written = ::write(signalPipe[1], &byte, 1);
    }

    void quitOnSignal(QCoreApplication &app)
    {
        if (::socketpair(AF_UNIX, SOCK_STREAM, 0, signalPipe) != 0)
            return;

        auto *notifier = new QSocketNotifier(signalPipe[0], QSocketNotifier::Read, &app);
        QObject::connect(notifier, &QSocketNotifier::activated, &app, [&app, notifier] {
            notifier->setEnabled(false);
            char                           byte = 0;
            [[maybe_unused]] const ssize_t read = ::read(signalPipe[0], &byte, 1);
            app.quit();
        });

        std::signal(SIGINT, onSignal);
        std::signal(SIGTERM, onSignal);
    }
} // namespace

// Everything main does once the arguments are understood, so that one
// try/catch can stand in front of all of it. A scene that names a file it
// does not have throws from deep in the render, and with nothing catching
// it the process aborted: `libc++abi: terminating due to uncaught exception`
// in front of a message that was actually useful.
static int run(argparse::ArgumentParser &parser, int argc, char *argv[])
{
    // The scene as the editor's timeline reads it. `videocode/serialize.py`'s own
    // __main__ prints the baked stack instead — one entry per input per frame,
    // seventeen thousand lines for a scene of two shapes — which nothing can
    // read. This is the model the timeline is drawn from, and it is small.
    if (parser.get<bool>("--inspect")) {
        const std::string path = parser.get<std::string>("--file");
        std::ifstream     in(path);
        if (!in) {
            std::cerr << "--inspect: cannot read " << path << "\n";
            return EXIT_FAILURE;
        }
        const std::string source((std::istreambuf_iterator<char>(in)), std::istreambuf_iterator<char>());
        const py::dict    result = py::module::import("videocode.serialize")
                                       .attr("execSource")(source, path)
                                       .cast<py::dict>();
        if (!result["ok"].cast<bool>()) {
            std::cerr << path << ":" << result["line"].cast<int>() + 1 << ": "
                      << result["message"].cast<std::string>() << "\n";
            return EXIT_FAILURE;
        }
        std::cout << result["scene"].cast<std::string>() << "\n";
        return EXIT_SUCCESS;
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

    // The editing shell. The scene graph's backend has to be settled before any
    // QQuickWindow exists, which means before the QApplication.
    const bool checksChrome = parser.get<bool>("--check-chrome");
    const bool wantsEditor = parser.get<bool>("--editor") || checksChrome;
    if (wantsEditor)
        VC::Editor::configureGraphicsApi();

    // What macOS puts in the Dock, the app menu and the ⌘-Tab switcher. Without
    // it the name is the executable's, which is a filename — lower case, hyphen
    // and all — rather than the product's.
    QCoreApplication::setApplicationName(QStringLiteral("Video-Code"));
    QGuiApplication::setApplicationDisplayName(QStringLiteral("Video-Code"));

    QApplication app(argc, argv);
    quitOnSignal(app);

    if (wantsEditor) {
        // `--file` names the scene here too. It used to be read by the renderer
        // alone, so `--editor --file x.py` opened whatever the working directory
        // happened to hold and said nothing about it — a flag accepted and then
        // dropped. Typed now, it outranks an exported VC_SCENE_FILE, the way a
        // flag on the line always outranks the environment it inherited.
        if (parser.is_used("--file"))
            qputenv("VC_SCENE_FILE", QByteArray::fromStdString(parser.get<std::string>("--file")));

        VC::Editor editor;
        editor.setHeadless(checksChrome);
        if (!editor.load())
            return EXIT_FAILURE;
        if (checksChrome) {
            // `load()` already said whether every QML file parsed and every
            // binding resolved — which is the whole question when there is no
            // picture to take.
            std::cout << "chrome loaded\n";
            if (!parser.is_used("--screenshot"))
                return EXIT_SUCCESS;

            // With one, the loop has to turn first. The chrome runs the scene
            // through `Qt.callLater`, so a capture taken before any event is
            // delivered photographs an empty timeline and an unpainted preview —
            // a picture of the chrome having done nothing yet.
            const QString shot = QString::fromStdString(parser.get<std::string>("--screenshot"));
            const int     settle = qEnvironmentVariableIntValue("VC_SETTLE") > 0
                                       ? qEnvironmentVariableIntValue("VC_SETTLE")
                                       : 1500;
            editor.probeClicks(settle);
            QTimer::singleShot(settle, &editor, [&editor, shot] {
                editor.captureHidden(shot);
                QCoreApplication::quit();
            });
            return app.exec();
        }
        if (parser.is_used("--screenshot"))
            editor.captureTo(QString::fromStdString(parser.get<std::string>("--screenshot")));
        return app.exec();
    }

    // Preview the video
    VC::Window window(parser);
    return app.exec();
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

    try {
        return run(parser, argc, argv);
    } catch (const std::exception &e) {
        // The message the throw carried, and nothing else: a person reading
        // it wants the file they got wrong, not the runtime's opinion of it.
        std::cerr << "video-code: " << e.what() << std::endl;
        return EXIT_FAILURE;
    }
}

// binding python / cpp

// boucle sens prediction video martin baldinger
