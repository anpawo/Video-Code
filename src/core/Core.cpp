/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Core
*/

#include "core/Core.hpp"

#include <qapplication.h>
#include <qpainter.h>
#include <qscreen.h>

#include <cstddef>
#include <cstdio>
#include <cstdlib>
#include <iostream>
#include <memory>
#include <opencv2/core/mat.hpp>
#include <opencv2/imgcodecs.hpp>
#include <opencv2/imgproc.hpp>
#include <string>

#include "input/IInput.hpp"
#include "input/InputFactory.hpp"
#include "input/media/Audio.hpp"
#include "input/media/Video.hpp"
#include "utils/Debug.hpp"
#include "utils/Exception.hpp"

VC::Core::Core(const argparse::ArgumentParser& parser)
    : _showstack(parser.get<bool>("--showstack"))
    , _showtimeline(parser.get<bool>("--showtimeline"))
    // ---
    , _width(parser.get<int>("--width"))
    , _height(parser.get<int>("--height"))
    // ---
    , _framerate(parser.get<int>("--framerate"))
    // ---
    , _sourceFile(parser.get("--file"))
    , _outputFile(parser.get("--generate"))
    // ---
    , _bgFrame(cv::Mat(_height, _width, CV_8UC4).setTo(cv::Scalar(0, 0, 0, 0)))
{
    reloadSourceFile();
}

void VC::Core::reloadSourceFile()
{
    std::string serializedScene;

    try {
        serializedScene = serializeScene();
    } catch (const Error& e) {
        std::cerr << "\nVideoCode: Invalid source file '" << _sourceFile << "', could not parse the instructions." << std::endl;
        return;
    }

    _inputs.clear();
    _stack.clear();
    _audioTracks.clear();

    try {
        _stack = json::parse(serializedScene);
    } catch (const std::exception& e) {
        std::cerr << "\nVideoCode: Couldn't parse source file: " << e.what() << std::endl;
        return;
    }

    executeStack();
}

std::string VC::Core::serializeScene()
{
    std::string command = std::format(
        "python3 -c \"import sys; sys.path.append('./videocode');from serialize import serializeScene; print(serializeScene('{}', {}))\"",
        _sourceFile,
        _framerate
    );
    FILE* pipe = popen(command.c_str(), "r");
    if (!pipe) {
        throw Error("Failed to load '" + _sourceFile + "'.");
    }

    char buffer[4096];
    std::string result;
    while (fgets(buffer, sizeof(buffer), pipe) != nullptr) {
        result += buffer;
    }

    return result;
}

void VC::Core::executeStack()
{
    for (auto& s : _stack) {
        if (_showstack) {
            std::cout << s << std::endl;
        }

        if (s["action"] == "Create") {
            if (s["type"] == "Video") {
                s["args"]["projectFps"] = static_cast<double>(_framerate);
            }
            _inputs.push_back(Factory::inputs.at(s["type"])(s["args"]));

            if (s["type"] == "Video") {
                auto* video = dynamic_cast<Video*>(_inputs.back().get());

                if (video->_nbFrame > _nbFrame) {
                    _nbFrame = video->_nbFrame;
                }
            }

            if (s["type"] == "Audio") {
                auto* audioInput = dynamic_cast<Audio*>(_inputs.back().get());

                double startSec = 0.0;
                if (s["args"].contains("startSec")) {
                    startSec = s["args"]["startSec"].get<double>();
                }

                _audioTracks.push_back({
                    audioInput->_filepath,
                    audioInput->_volume,
                    startSec,
                });
            }

        } else if (s["action"] == "Apply") {
            ssize_t index = s["input"];

            size_t start = s["args"]["start"];
            size_t duration = s["args"]["duration"];
            size_t lastFrame = start + duration;

            if (lastFrame > _nbFrame) {
                _nbFrame = lastFrame;
            }
            _inputs[index]->add(s);

        } else if (s["action"] == "Wait") {
            size_t n = s["n"];

            for (size_t i = 0; i < n; i++) {
                _waits[_nbFrame + i] = _nbFrame == 0 ? 0 : (_nbFrame - 1);
            }
            _nbFrame += n;

        } else {
            throw Error("Invalid action: " + s["action"].get<std::string>());
        }
    }
}

cv::Mat VC::Core::generateFrame(size_t index)
{
    cv::Mat bg = _bgFrame.clone();

    auto potentialIndex = _waits.find(index);

    if (potentialIndex != _waits.end()) {
        index = potentialIndex->second;
    }

    for (auto& i : _inputs) {
        i->overlay(bg, index);
    }

    return bg;
}

void VC::Core::updateFrame(QLabel& imageLabel)
{
    if (!_indexChanged) {
        return;
    }

    cv::Mat frame = generateFrame(_index);

    // Screen pixel density ratio (needed for mac's retina)
    qreal scaleFactor = qApp->devicePixelRatio();

    cv::resize(
        frame,
        frame,
        cv::Size(
            _width / (2.0 / scaleFactor),
            _height / (2.0 / scaleFactor)
        ),
        _width / (2.0 / scaleFactor),
        _height / (2.0 / scaleFactor),
        cv::INTER_LINEAR
    );

    // load next frame if not in pause and not at the end
    if (_paused == false && _nbFrame && _index < _nbFrame - 1) {
        _index += 1;
        _indexChanged = true;
    } else {
        _indexChanged = false;
    }

    // Create QImage from frame data
    QImage img(frame.data, frame.cols, frame.rows, frame.step, QImage::Format_ARGB32);
    img.setDevicePixelRatio(qApp->devicePixelRatio());

    // Create a pixmap for better display (cpu)
    QPixmap pixmap = QPixmap::fromImage(img);
    imageLabel.setPixmap(pixmap);
}

int VC::Core::generateVideo()
{
    // If we have audio tracks, first generate a temp video, then mux with audio
    bool hasAudio = !_audioTracks.empty();
    std::string videoTarget = hasAudio ? _outputFile + ".tmp.mp4" : _outputFile;

    FILE* ffmpegPipe = popen(
        std::format(
            "ffmpeg"
            " -y"                   // override existing file
            " -f rawvideo"          // rawvideo codec (the pipe receives pixels in stdin)
            " -pixel_format bgra"   // the format of the pixel sent
            " -video_size {}x{}"    // width and height
            " -framerate {}"        // input framerate
            " -an"                  // no audio in raw pipe
            " -i -"                 // the inputs comes from a pipe (stdin)
            " -c:v libx264"         // the codec defines how are the frames compressed in the output file
            " -preset veryfast"     // speed up the process
            " -pix_fmt yuv420p"     // the pixel format defines how the colors are represented in the file
            " -crf 23"              // video quality (recommended for libx264)
            " -movflags +faststart" // metadata is at the start of the video so it can start playing even if not full loaded
            " -loglevel warning"    // display only warnings
            " {}",                  // output filename
            _width,
            _height,
            _framerate,
            videoTarget
        )
            .c_str(),
        "w"
    );

    if (!ffmpegPipe) {
        throw Error("Could not start the ffmpeg pipe.");
    }

    for (size_t i = 0; i < _nbFrame; i++) {
        cv::Mat f = generateFrame(i);

        if (f.rows != _height && f.cols != _width) {
            throw Error("index: " + std::to_string(i) + ". Frame size mismatch. width: " + std::to_string(f.cols) + "!=" + std::to_string(_width) + ", height: " + std::to_string(f.rows) + "!=" + std::to_string(_height));
        }

        if (!f.isContinuous()) {
            f = f.clone();
        }

        size_t bytes = f.total() * f.elemSize();
        size_t written = fwrite(f.data, 1, bytes, ffmpegPipe);

        if (written != bytes) {
            throw Error("index: " + std::to_string(i) + ". Wrote only " + std::to_string(written) + " out of " + std::to_string(bytes) + " bytes.");
        }
    }

    pclose(ffmpegPipe);

    // Mux audio tracks if any
    if (hasAudio) {
        std::string cmd = "ffmpeg -y -i " + videoTarget;

        // Add audio inputs
        for (const auto& track : _audioTracks) {
            cmd += " -i \"" + track.filepath + "\"";
        }

        // Build filter_complex for audio mixing
        if (_audioTracks.size() == 1) {
            // Single audio track: apply volume and delay
            const auto& track = _audioTracks[0];
            cmd += std::format(
                " -filter_complex \"[1:a]volume={},adelay={}|{}[aout]\"",
                track.volume,
                static_cast<int>(track.startSec * 1000),
                static_cast<int>(track.startSec * 1000)
            );
            cmd += " -map 0:v -map \"[aout]\"";
        } else {
            // Multiple audio tracks: mix them together
            cmd += " -filter_complex \"";
            for (size_t i = 0; i < _audioTracks.size(); i++) {
                const auto& track = _audioTracks[i];
                cmd += std::format(
                    "[{}:a]volume={},adelay={}|{}[a{}];",
                    i + 1,
                    track.volume,
                    static_cast<int>(track.startSec * 1000),
                    static_cast<int>(track.startSec * 1000),
                    i
                );
            }
            // Merge all audio streams
            for (size_t i = 0; i < _audioTracks.size(); i++) {
                cmd += std::format("[a{}]", i);
            }
            cmd += std::format("amix=inputs={}:duration=longest[aout]\"", _audioTracks.size());
            cmd += " -map 0:v -map \"[aout]\"";
        }

        cmd += " -c:v copy -c:a aac -b:a 192k";
        cmd += " -movflags +faststart -loglevel warning";
        cmd += " " + _outputFile;

        int ret = system(cmd.c_str());

        // Clean up temp file
        std::remove(videoTarget.c_str());

        if (ret != 0) {
            throw Error("Failed to mux audio into video.");
        }
    }

    VC_LOG_DEBUG("video generated as: " + _outputFile)
    return 0;
}

int VC::Core::generateImage(const std::string& format)
{
    std::string ext = (format == "jpg" || format == "jpeg") ? ".jpg" : ".png";

    if (_nbFrame == 0) {
        throw Error("No frames to export.");
    }

    if (_nbFrame == 1) {
        // Single frame: export directly with the output filename
        cv::Mat f = generateFrame(0);
        std::string filename = _outputFile;

        // Replace extension if output file has a video extension
        size_t dotPos = filename.rfind('.');
        if (dotPos != std::string::npos) {
            filename = filename.substr(0, dotPos) + ext;
        } else {
            filename += ext;
        }

        // Convert BGRA to BGR for imwrite (drop alpha)
        cv::Mat output;
        cv::cvtColor(f, output, cv::COLOR_BGRA2BGR);
        cv::imwrite(filename, output);

        VC_LOG_DEBUG("image generated as: " + filename)
    } else {
        // Multiple frames: export as image sequence
        for (size_t i = 0; i < _nbFrame; i++) {
            cv::Mat f = generateFrame(i);

            std::string filename = std::format("frame_{:06d}{}", i, ext);

            cv::Mat output;
            cv::cvtColor(f, output, cv::COLOR_BGRA2BGR);
            cv::imwrite(filename, output);
        }

        VC_LOG_DEBUG("image sequence generated: " + std::to_string(_nbFrame) + " frames")
    }

    return 0;
}

#define currIndex(i, s) (s == 0 ? 0 : (i + 1))

void VC::Core::pause()
{
    _paused = !_paused;
    _indexChanged = true;
    std::cout << std::format("Timeline {} at frame {}/{}.", _paused ? "paused" : "unpaused", currIndex(_index, _nbFrame), _nbFrame) << std::endl;
}

void VC::Core::goToFirstFrame()
{
    if (_index != 0) {
        _index = 0;
        _indexChanged = true;
    }
    std::cout << std::format("Jumped backward to the first frame {}/{}.", currIndex(_index, _nbFrame), _nbFrame) << std::endl;
}

void VC::Core::goToLastFrame()
{
    if (_nbFrame != 0) {
        _index = _nbFrame - 1;
        _indexChanged = true;
    }
    std::cout << std::format("Jumped forward to the last frame {}/{}.", currIndex(_index, _nbFrame), _nbFrame) << std::endl;
}

void VC::Core::backward1frame()
{
    if (_index > 0) {
        _index -= 1;
        _indexChanged = true;
    }
    std::cout << std::format("Jumped backward to the frame {}/{}.", currIndex(_index, _nbFrame), _nbFrame) << std::endl;
}

void VC::Core::forward1frame()
{
    if (_index + 1 < _nbFrame) {
        _index += 1;
        _indexChanged = true;
    }
    std::cout << std::format("Jumped forward to the frame {}/{}.", currIndex(_index, _nbFrame), _nbFrame) << std::endl;
}
