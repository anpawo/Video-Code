/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** generateVideo
*/

#include <cstdio>
#include <format>

#include "compiler/Compiler.hpp"
#include "opencv2/core/matx.hpp"
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
            " -y"                 // override existing file
            " -f rawvideo"        // rawvideo codec (the pipe receives pixels in stdin)
            " -pixel_format rgba" // the format of the pixel sent
            " -video_size {}x{}"  // width and height
            " -framerate {}"      // fps
            " -an"                // tells ffmpeg to expect no audio
            " -i -"               // the inputs comes from a pipe (stdin)
            " -codec:v libx264"   // the codec defines how are the frames compressed in the output file
            " -pix_fmt yuv420p"   // the pixel format defines how the colors are represented in the file
            " -crf 23"            // video quality (recommended for libx264)
            " -loglevel warning"  // display only warnings
            " {}",                // output filename
            width,
            height,
            fps,
            filename
        )
            .c_str(),
        "w"
    );

    if (!ffmpegPipe) {
        throw Error("Could not start the ffmpeg pipe.");
    }

    for (const auto &f : frames) {
        const int nbRows = f.rows;
        const int nbCols = f.cols;

        cv::Mat frame(nbRows, nbCols, CV_8UC4); // BGRA -> RGBA

        for (int y = 0; y < nbRows; y++) {
            for (int x = 0; x < nbCols; x++) {
                const cv::Vec4b pixel = f.at<cv::Vec4b>(y, x);

                const float alpha = pixel[3] / 255.0;

                frame.at<cv::Vec4b>(y, x) = {
                    cv::saturate_cast<uchar>(pixel[2] * alpha), // r
                    cv::saturate_cast<uchar>(pixel[1] * alpha), // g
                    cv::saturate_cast<uchar>(pixel[0] * alpha), // b
                    pixel[3]                                    // a
                };
            }
        }

        fwrite(frame.data, 1, frame.total() * frame.elemSize(), ffmpegPipe);
        fflush(ffmpegPipe);
    }

    pclose(ffmpegPipe);

    VC_LOG_DEBUG("video generated as: " + filename)

    return 0;
}
