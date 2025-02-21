/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** generateVideo
*/

#include <cstdio>
#include <format>

#include "compiler/Compiler.hpp"
#include "opencv2/imgcodecs.hpp"
#include "opencv2/imgproc.hpp"
#include "utils/Debug.hpp"
#include "utils/Exception.hpp"

int Compiler::Writer::generateVideo(
    int width,
    int height,
    int fps,
    std::string filename,
    const std::vector<cv::Mat> &frames
)
{
    FILE *ffmpegPipe = popen(
        std::format(
            "ffmpeg"
            " -y"                    // override existing file
            " -f rawvideo"           // rawvideo codec
            " -pixel_format rgba"    // red green blue alpha
            " -video_size {}x{}"     // width and height
            " -framerate {}"         // fps
            " -an"                   // tells ffmpeg to expect no audio
            " -i -"                  // the inputs comes from stdin (pipe)
            " -c:v prores_ks"        // Use VP9 codec (supports alpha)
            " -pix_fmt yuva444p10le" // Ensure alpha channel is preserved
            " -loglevel warning"     // display only warnings
            " {}",                   // output filename
            width,
            height,
            fps,
            filename
        )
            .c_str(),
        "w"
    );

    if (!ffmpegPipe)
    {
        throw Error("Could not start the ffmpeg pipe.");
    }

    int i = 0;
    for (const auto &frame : frames)
    {
        i++;
        cv::Mat rgba_frame = frame;
        cv::cvtColor(frame, rgba_frame, cv::COLOR_BGRA2RGBA);

        if (i > 10)
        {
            break;
        }

        fwrite(rgba_frame.data, 1, rgba_frame.total() * rgba_frame.elemSize(), ffmpegPipe);
        fflush(ffmpegPipe);
    }

    pclose(ffmpegPipe);

    VC_LOG_DEBUG("video generated as:")
    VC_LOG_DEBUG(filename.c_str())

    return 0;
}
