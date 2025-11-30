/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Core
*/

#include "core/Core.hpp"

#include <iostream>
#include <memory>
#include <opencv2/core/mat.hpp>
#include <string>

#include "core/Factory.hpp"
#include "python/API.hpp"
#include "utils/Debug.hpp"

VC::Core::Core(const argparse::ArgumentParser& parser)
    : _width(parser.get<int>("--width"))
    , _height(parser.get<int>("--height"))
    , _framerate(parser.get<int>("--framerate"))
    , _sourceFile(parser.get("--file"))
    , _outputFile(parser.get("--generate"))
    , _showstack(parser.get<bool>("--showstack"))
    , _timeit(parser.get<bool>("--time"))
    , _bgFrame(cv::Mat(_height, _width, CV_8UC4).setTo(cv::Scalar(0, 0, 0, 0)))
    , _camera(new Camera(_bgFrame.clone(), {}))
{
    python::API::initialize();
    reloadSourceFile();
}

VC::Core::~Core()
{
    python::API::finalize();
}

void VC::Core::reloadSourceFile()
{
    std::string serializedScene;

    try {
        serializedScene = python::API::call<std::string>("Serialize", "serializeScene", _sourceFile);
    } catch (const Error& e) {
        std::cerr << "\nVideoCode: Invalid source file '" << _sourceFile << "', could not parse the instructions." << std::endl;
        return;
    }

    _frames.clear();
    _inputs.clear();
    _addedInputs.clear();
    _stack.clear();

    _stack = json::parse(serializedScene);

    executeStack();
    addNewFrames();
}

#define CAMERA (-1)

void VC::Core::executeStack()
{
    for (auto& s : _stack) {
        if (_showstack) {
            std::cout << s << std::endl;
        }

        if (s["action"] == "Create") {
            _inputs.push_back(Factory::create(s["type"], s));
        } else if (s["action"] == "Add") {
            ssize_t index = s["input"];

            if (index == CAMERA) {
                _camera->flushTransformation();
            } else {
                _inputs[index]->flushTransformation();
                if (std::find(_addedInputs.begin(), _addedInputs.end(), index) == _addedInputs.end()) {
                    _addedInputs.push_back(index);
                }
            }
        } else if (s["action"] == "Apply") {
            ssize_t index = s["input"];

            s["args"]["duration"] = s["args"]["duration"].get<double>() * _framerate;
            s["args"]["start"] = s["args"]["start"].get<double>() * _framerate;

            if (index == CAMERA) {
                _camera->apply(s["transformation"], s["args"]);
            } else {
                _inputs[index]->apply(s["transformation"], s["args"]);
            }
        } else if (s["action"] == "Wait") {
            addNewFrames();

            for (size_t n = s["n"].get<size_t>() * _framerate; n; n--) {
                if (_frames.empty()) {
                    _frames.push_back(_bgFrame.clone());
                } else {
                    _frames.push_back(_frames.back().clone());
                }
            }
        }
    }
}

void VC::Core::addNewFrames()
{
    bool anythingChanged = _addedInputs.size();

    while (anythingChanged) {
        anythingChanged = false;

        _camera->resetCurrentFrameToBase();
        _camera->applySetters();
        Frame& frame = _camera->getCurrentFrame();

        for (auto i : _addedInputs) {
            _inputs[i]->overlayLastFrame(frame.mat, frame.meta.position);
            anythingChanged |= _inputs[i]->frameHasChanged();
        }

        _camera->generateNextFrame();
        anythingChanged |= _camera->frameHasChanged();
        if (anythingChanged) {
            _frames.push_back(std::move(frame.mat));
        }
    }
}

void VC::Core::updateFrame(QLabel& imageLabel)
{
    cv::Mat frame;

    if (_frames.size() == 0) {
        // show black background if no frames are loaded
        cv::resize(_bgFrame, frame, cv::Size(_width / 2, _height / 2), _width / 2.0, 2.0, cv::INTER_LINEAR);
    } else {
        cv::resize(_frames[_index], frame, cv::Size(_width / 2, _height / 2), _width / 2.0, _height / 2.0, cv::INTER_LINEAR);

        // load next frame if not in pause and not at the end
        if (_paused == false && _index < _frames.size() - 1) {
            _index += 1;
        }
    }

    // convert to rgba because opencv stores it as bgra
    cv::cvtColor(frame, frame, cv::COLOR_BGRA2RGBA);

    // convert to pixmap for better display (cpu)
    QPixmap pixmap = QPixmap::fromImage(QImage(frame.data, frame.cols, frame.rows, frame.step, QImage::Format_RGBA8888));

    // update the currently shown image
    imageLabel.setPixmap(pixmap);
}

int VC::Core::generateVideo()
{
    FILE* ffmpegPipe = popen(
        std::format(
            "ffmpeg"
            " -y"                   // override existing file
            " -f rawvideo"          // rawvideo codec (the pipe receives pixels in stdin)
            " -pixel_format rgba"   // the format of the pixel sent
            " -video_size {}x{}"    // width and height
            " -framerate {}"        // input framerate
            " -an"                  // tells ffmpeg to expect no audio
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
            _outputFile
        )
            .c_str(),
        "w"
    );

    if (!ffmpegPipe) {
        throw Error("Could not start the ffmpeg pipe.");
    }

    for (const auto& f : _frames) {
        if (f.rows != _height && f.cols != _width) {
            throw Error("Frame size mismatch. width: " + std::to_string(f.cols) + "!=" + std::to_string(_width) + ", height: " + std::to_string(f.rows) + "!=" + std::to_string(_height));
        }

        cv::Mat frame;
        cv::cvtColor(f, frame, cv::COLOR_BGRA2RGBA); ///< BGRA -> RGBA

        if (!frame.isContinuous()) {
            frame = frame.clone();
        }

        size_t bytes = frame.total() * frame.elemSize();
        size_t written = fwrite(frame.data, 1, bytes, ffmpegPipe);

        if (written != bytes) {
            throw Error("Wrote only " + std::to_string(written) + " out of " + std::to_string(bytes) + " bytes.");
        }
    }

    pclose(ffmpegPipe);
    VC_LOG_DEBUG("video generated as: " + _outputFile)
    return 0;
}

#define currIndex(i, s) (s == 0 ? 0 : (i + 1))

void VC::Core::pause()
{
    _paused = !_paused;
    std::cout << std::format("Timeline {} at frame {}/{}.", _paused ? "paused" : "unpaused", currIndex(_index, _frames.size()), _frames.size()) << std::endl;
}

void VC::Core::goToFirstFrame()
{
    _index = 0;
    std::cout << std::format("Jumped backward to the first frame {}/{}.", currIndex(_index, _frames.size()), _frames.size()) << std::endl;
}

void VC::Core::goToLastFrame()
{
    if (_frames.size()) {
        _index = _frames.size() - 1;
    }
    std::cout << std::format("Jumped forward to the last frame {}/{}.", currIndex(_index, _frames.size()), _frames.size()) << std::endl;
}

void VC::Core::backward1frame()
{
    if (_index < 1) {
        _index = 0;
    } else {
        _index -= 1;
    }
    std::cout << std::format("Jumped backward to the frame {}/{}.", currIndex(_index, _frames.size()), _frames.size()) << std::endl;
}

void VC::Core::forward1frame()
{
    _index += 1;
    if (_index > _frames.size()) {
        _index = _frames.size() - 1;
    }
    std::cout << std::format("Jumped forward to the frame {}/{}.", currIndex(_index, _frames.size()), _frames.size()) << std::endl;
}
