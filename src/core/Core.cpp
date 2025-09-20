/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Core
*/

#include "core/Core.hpp"

#include "core/Factory.hpp"
#include "python/API.hpp"
#include "utils/Debug.hpp"

VC::Core::Core(const argparse::ArgumentParser& parser)
    : _width(parser.get<int>("--width"))
    , _height(parser.get<int>("--height"))
    , _framerate(parser.get<int>("--framerate"))
    , _sourceFile(parser.get("--sourceFile"))
    , _outputFile(parser.get("--generate"))
    , _bgFrame(cv::Mat(_height, _width, CV_8UC4).setTo(cv::Scalar(0, 0, 0, 0)))
{
    reloadSourceFile();
}

VC::Core::~Core() = default;

void VC::Core::reloadSourceFile()
{
    std::string serializedScene;

    try {
        serializedScene = python::API::call<std::string>("Serialize", "serializeScene", _sourceFile);
    } catch (const Error& e) {
        std::cout << "Invalid source file, could not parse the instructions." << std::endl;
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

void VC::Core::executeStack()
{
    for (auto& i : _stack) {
        VC_LOG_DEBUG(i);

        if (i["action"] == "Create") {
            _inputs.push_back(Factory::create(i["type"], i));
        } else if (i["action"] == "Add") {
            size_t index = i["input"];
            _inputs[index]->flushTransformation();
            if (std::find(_addedInputs.begin(), _addedInputs.end(), index) == _addedInputs.end()) {
                _addedInputs.push_back(index);
            }
        } else if (i["action"] == "Apply") {
            i["args"]["duration"] = i["args"]["duration"].get<size_t>() * _framerate;
            i["args"]["start"] = i["args"]["start"].get<size_t>() * _framerate;
            _inputs[i["input"]]->apply(i["transformation"], i["args"]);
        } else if (i["action"] == "Wait") {
            addNewFrames();
            for (size_t n = i["n"].get<size_t>() * _framerate; n; n--) {
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
    bool anyInputChanged = _addedInputs.size();

    while (anyInputChanged) {
        anyInputChanged = false;

        cv::Mat frame = _bgFrame.clone();

        for (auto i : _addedInputs) {
            _inputs[i]->overlayLastFrame(frame);

            anyInputChanged |= _inputs[i]->frameHasChanged();
        }

        _frames.push_back(std::move(frame));
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

    VC_LOG_DEBUG("video generated as: " + _outputFile)

    return 0;
}

void VC::Core::pause()
{
    _paused = !_paused;
    std::cout << std::format("Timeline {} at frame {}/{}.", _paused ? "paused" : "unpaused", _index, _frames.size() - 1) << std::endl;
}

void VC::Core::goToFirstFrame()
{
    _index = 0;
    std::cout << std::format("Jumped backward to the first frame of the video: {}", _index) << std::endl;
}

void VC::Core::goToLastFrame()
{
    if (_frames.size()) {
        _index = _frames.size() - 1;
    }
    std::cout << std::format("Jumped forward to the last frame of the video: {}", _index) << std::endl;
}

void VC::Core::backward3frames()
{
    if (_index < 3 * _framerate) {
        _index = 0;
    } else {
        _index -= 3 * _framerate;
    }
}

void VC::Core::forward3frames()
{
    _index += 3 * _framerate;
    if (_index > _frames.size()) {
        _index = _frames.size() - 1;
    }
}
