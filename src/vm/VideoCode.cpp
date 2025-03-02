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

#include <algorithm>
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

VideoCode::VideoCode(int argc, char **argv, int width, int height, std::string sourceFile, bool generate, std::string outputFile)
    : _width(width)
    , _height(height)
    , _sourceFile(sourceFile)
    , _defaultBlackFrame(cv::Mat(height, width, CV_8UC4).setTo(cv::Scalar(0, 0, 0, 255)))
{
    ///< Parse the source file
    reloadSourceFile();

    if (generate)
    {
        _outputFile = outputFile;
    }
    else
    {
        ///< If we want to edit the video, we create the window for it
        _app.reset(new AppWindow(argc, argv, _events, _sourceFile, _width, _height, _frameRate, [this](QLabel &imageLabel) { this->updateFrame(imageLabel); }));
    }
}

void VideoCode::reloadSourceFile()
{
    ///< TODO: add a cache
    _frames.clear();

    std::string serializedScene;

    try
    {
        serializedScene = python::API::call<std::string>("Serialize", "serializeScene", _sourceFile);
    } catch (const Error &e)
    {
        std::cout << "Invalid source file, could not parse the instructions." << std::endl;
        return;
    }

    json::object_t dict = json::parse(serializedScene);

    json::array_t newRequiredInputs = dict["requiredInputs"];
    json::array_t newActionStack = dict["actionStack"];

    VC_LOG_DEBUG(newRequiredInputs);
    VC_LOG_DEBUG(newActionStack);

    _register.updateInstructions(std::move(newRequiredInputs));
    _actionStack = std::move(newActionStack);

    executeStack();

    std::cout << _labels << std::endl;
    std::cout << _labelsByVal << std::endl;
}

void VideoCode::executeStack()
{
    for (const auto &i : _actionStack)
    {
        if (i["action"] == "Add")
        {
            ///< Example: {"action": 'Add', "input": 0}
            addFrames(_register[i["input"]]);
        }
        else if (i["action"] == "Apply")
        {
            ///< Example: {"action": 'Apply', "input": 0, "transformation": 'overlay', "fg": 1}
            transformation::map.at(i["transformation"])(_register[i["input"]], _register, i["args"]);
        }
    }
}

void VideoCode::updateFrame(QLabel &imageLabel)
{
    cv::Mat frame;

    if (_frames.size() == 0)
    {
        // show black background if no frames are loaded
        cv::resize(_defaultBlackFrame, frame, cv::Size(_width / 2, _height / 2), _width / 2.0, 0, cv::INTER_LINEAR);
    }
    else
    {
        cv::resize(_frames[_index], frame, cv::Size(_width / 2, _height / 2), _width / 2.0, 0, cv::INTER_LINEAR);

        // load next frame if not in pause and not at the end
        if (_paused == false && _index < _frames.size() - 1)
        {
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
    if (_app == nullptr)
    {
        return Compiler::Writer::generateVideo(_width, _height, _frameRate, _outputFile, _frames);
    }
    else
    {
        return _app->run();
    }
}

void VideoCode::goToLabel(const std::string &label)
{
    auto it = _labels.find(label);

    if (it != _labels.end())
    {
        _index = it->second;
        _currentLabel = label;
    }
}

void VideoCode::addLabel(const std::string &label, std::size_t index)
{
    // update the current label if we override it
    if (_labels[_currentLabel] == index)
    {
        _currentLabel = label;
    }
    // erase any label with the same value
    if (_labelsByVal.contains(index))
    {
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

void VideoCode::addFrames(const std::shared_ptr<IInput> frames)
{
    for (const auto &[mat, meta] : *frames)
    {
        addFrame(mat, meta);
    }
}

void VideoCode::addFrame(const cv::Mat &mat, const Metadata &meta)
{
    cv::Mat frame = _defaultBlackFrame.clone();

    // Calculate the source rectangle
    int srcX = std::max(0, -meta.x);
    int srcY = std::max(0, -meta.y);
    int srcWidth = std::min(mat.cols - srcX, frame.cols);
    int srcHeight = std::min(mat.rows - srcY, frame.rows);

    // Calculate the destination rectangle
    int dstX = std::max(0, meta.x);
    int dstY = std::max(0, meta.y);
    int dstWidth = srcWidth;
    int dstHeight = srcHeight;

    // Ensure the destination rectangle is within the frame bounds
    dstWidth = std::min(dstWidth, frame.cols - dstX);
    dstHeight = std::min(dstHeight, frame.rows - dstY);

    // Adjust the source rectangle if the destination rectangle was reduced
    srcWidth = dstWidth;
    srcHeight = dstHeight;

    // Define the source and destination regions
    cv::Rect src(srcX, srcY, srcWidth, srcHeight);
    cv::Rect dst(dstX, dstY, dstWidth, dstHeight);

    // Only copy if we have valid regions
    if (src.width > 0 && src.height > 0 && dst.width > 0 && dst.height > 0)
    {
        mat(src).copyTo(frame(dst));
    }
    _frames.push_back(frame);
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

void VideoCode::goToPreviousLabel()
{
    if (_labels[_currentLabel] == 0)
    {
        goToLabel(_currentLabel);
        std::cout << std::format("Timeline set to the start of the current label '{}', at frame '{}'.", _currentLabel, _index) << std::endl;
    }
    else
    {
        goToLabel(std::prev(_labelsByVal.find(_labels[_currentLabel]))->second);
        std::cout << std::format("Timeline set to the previous label '{}', at frame '{}'.", _currentLabel, _index) << std::endl;
    }
}

void VideoCode::goToNextLabel()
{
    auto next = std::next(_labelsByVal.find(_labels[_currentLabel]));

    if (next == _labelsByVal.end())
    {
        _index = _frames.size() - 1;
        std::cout << std::format("Timeline set to last index, '{}'", _index) << std::endl;
    }
    else
    {
        goToLabel(next->second);
        std::cout << std::format("Timeline set to the next label '{}', at frame '{}'.", _currentLabel, _index) << std::endl;
    }
}
