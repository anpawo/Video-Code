/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** LiveWindow
*/

#include "vm/VideoCode.hpp"

#include <qapplication.h>
#include <qboxlayout.h>
#include <qimage.h>
#include <qlabel.h>
#include <qobject.h>
#include <qpixmap.h>
#include <qpushbutton.h>
#include <qtimer.h>
#include <unistd.h>

#include <cstddef>
#include <cstdlib>
#include <format>
#include <iostream>
#include <iterator>
#include <memory>
#include <opencv2/core/mat.hpp>
#include <opencv2/core/matx.hpp>
#include <opencv2/highgui.hpp>
#include <opencv2/imgproc.hpp>
#include <string>

#include "compiler/Compiler.hpp"
#include "opencv2/core/types.hpp"
#include "python/API.hpp"
#include "transformation/transformation.hpp"
#include "utils/Debug.hpp"
#include "utils/Exception.hpp"
#include "utils/Map.hpp"
#include "vm/AppWindow.hpp"
#include "vm/Factory.hpp"

VideoCode::VideoCode(int argc, char **argv, int width, int height, std::string sourceFile, bool generate, std::string outputFile)
    : _width(width)
    , _height(height)
    , _sourceFile(sourceFile)
    , _defaultBlackFrame(cv::Mat(height, width, CV_8UC4).setTo(cv::Scalar(0, 0, 0, 0)))
{
    ///< Parse the source file
    reloadSourceFile();

    if (generate) {
        _outputFile = outputFile;
    }
    else {
        ///< If we want to edit the video, we create the window for it
        _app.reset(new AppWindow(argc, argv, _events, _sourceFile, _width, _height, _framerate, [this](QLabel &imageLabel) { this->updateFrame(imageLabel); }));
    }
}

void VideoCode::reloadSourceFile()
{
    std::string serializedScene;

    try {
        serializedScene = python::API::call<std::string>("Serialize", "serializeScene", _sourceFile);
    } catch (const Error &e) {
        std::cout << "Invalid source file, could not parse the instructions." << std::endl;
        return;
    }

    json::array_t stack = json::parse(serializedScene);

    _stack = std::move(stack);

    executeStack();
    addNewFrames();

    std::cout << _labels << std::endl;
    std::cout << _labelsByVal << std::endl;
}

void VideoCode::executeStack()
{
    _inputs.clear();

    for (auto &i : _stack) {
        VC_LOG_DEBUG(i);

        if (i["action"] == "Create") {
            _inputs.push_back(Factory::create(i["type"], i, _inputs));
        }
        else if (i["action"] == "Add") {
            _addedInputs.push_back(i["input"]);
        }
        else if (i["action"] == "Apply") {
            i["args"]["duration"] = i["args"]["duration"].get<size_t>() * _framerate;
            i["args"]["width"] = _width;
            i["args"]["height"] = _height;
            _inputs[i["input"]]->apply(i["transformation"], i["args"]);
        }
        else if (i["action"] == "Wait") {
            for (size_t n = 0; n < i["n"]; n++) {
                if (_frames.empty()) {
                    _frames.push_back(_defaultBlackFrame.clone());
                }
                else {
                    _frames.push_back(_frames.back().clone());
                }
            }
        }
    }
}

void VideoCode::addNewFrames()
{
    _frames.clear();

    bool anyInputChanged = _addedInputs.size();

    while (anyInputChanged) {
        anyInputChanged = false;

        cv::Mat frame = _defaultBlackFrame.clone();

        for (auto i : _addedInputs) {
            _inputs[i]->overlayLastFrame(frame);

            anyInputChanged |= _inputs[i]->hasChanged();
        }

        _frames.push_back(std::move(frame));
    }
}

void VideoCode::updateFrame(QLabel &imageLabel)
{
    cv::Mat frame;

    if (_frames.size() == 0) {
        // show black background if no frames are loaded
        cv::resize(_defaultBlackFrame, frame, cv::Size(_width / 2, _height / 2), _width / 2.0, 2.0, cv::INTER_LINEAR);
    }
    else {
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

int VideoCode::run()
{
    if (_app == nullptr) {
        return Compiler::Writer::generateVideo(_width, _height, _framerate, _outputFile, _frames);
    }
    else {
        return _app->run();
    }
}

void VideoCode::goToLabel(const std::string &label)
{
    auto it = _labels.find(label);

    if (it != _labels.end()) {
        _index = it->second;
        _currentLabel = label;
    }
}

void VideoCode::addLabel(const std::string &label, std::size_t index)
{
    // update the current label if we override it
    if (_labels[_currentLabel] == index) {
        _currentLabel = label;
    }
    // erase any label with the same value
    if (_labelsByVal.contains(index)) {
        _labels.erase(_labelsByVal[index]);
    }

    _labelsByVal[index] = label;
    _labels[label] = index;
}

void VideoCode::removeLabel(const std::string &label)
{
    _labelsByVal.erase(_labels[label]);
    _labels.erase(label);
}

void VideoCode::pause()
{
    _paused = !_paused;
    std::cout << std::format("Timeline {} at frame '{}'.", _paused ? "paused" : "unpaused", _index) << std::endl;
}

void VideoCode::stop()
{
    _running = false;
    QApplication::quit();
}

void VideoCode::goToFirstFrame()
{
    goToLabel(_labelsByVal[0]);
    std::cout << std::format("Current Label set to '{}' at frame '0'.", _currentLabel) << std::endl;
}

void VideoCode::goToLastFrame()
{
    goToLabel(std::prev(_labelsByVal.end())->second);
    std::cout << std::format("Current Label set to '{}' at frame '{}'.", _currentLabel, _index) << std::endl;
}

void VideoCode::backward3frame()
{
    if (_index < 3 * _framerate) {
        _index = 0;
    }
    else {
        _index -= 3 * _framerate;
    }
}

void VideoCode::forward3frame()
{
    _index += 5 * _framerate;
    if (_index > _frames.size()) {
        _index = _frames.size() - 1;
    }
}
