/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** LiveWindow
*/

#include "vm/LiveWindow.hpp"

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
#include <format>
#include <iostream>
#include <opencv2/core/mat.hpp>
#include <opencv2/core/matx.hpp>
#include <opencv2/highgui.hpp>
#include <opencv2/imgproc.hpp>
#include <string>

#include "opencv2/core/types.hpp"
#include "python/API.hpp"
#include "transformation/transformation.hpp"
#include "utils/Exception.hpp"
#include "utils/Map.hpp"

LiveWindow::LiveWindow(int &argc, char **argv, int width, int height, std::string &&sourceFile)
    : _width(width)
    , _height(height)
    , _sourceFile(sourceFile)
    , _defaultBlackFrame(cv::Mat(height, width, CV_8UC4).setTo(cv::Scalar(0, 0, 0, 255)))
    , _app(argc, argv)
    , _window(_events, sourceFile, _width, _height, [this]() { this->updateFrame(); })
{
    ///< Setup the layouts and images
    _imageLayout.addWidget(&_imageLabel);
    _window.setLayout(&_imageLayout);

    ///< Connect the main loop with the window
    QObject::connect(&_timer, &QTimer::timeout, &_window, &WindowEvent::mainLoop);
    _timer.start(_frameRate);

    ///< Parse the source file
    reloadSourceFile();
}

LiveWindow::~LiveWindow()
{
    cv::destroyAllWindows();
}

void LiveWindow::reloadSourceFile()
{
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
    json::array_t newTransformationStack = dict["transformationStack"];

    std::cout << newRequiredInputs << std::endl;
    std::cout << newTransformationStack << std::endl;

    _register.updateInstructions(std::move(newRequiredInputs));
    _transformationStack = std::move(newTransformationStack);

    executeStack();

    std::cout << _labels << std::endl;
    std::cout << _labelsByVal << std::endl;
}

void LiveWindow::executeStack()
{
    for (const auto &t : _transformationStack)
    {
        if (t[0] == "Add")
        {
            ///< Example: ['Add', 0, []]
            addFrames(_register[t[1]]->getFrames());
        }
        else if (t[0] == "Apply")
        {
            ///< Example: ['Apply', 0, ['overlay', [1]]]
            transformation::map.at(t[2][0])(_register[t[1]], _register, t[2][1]);
        }
    }
}

void LiveWindow::updateFrame()
{
    cv::Mat frame;

    if (_frames.size() == 0)
    {
        // show black background if no frames are loaded
        cv::resize(_defaultBlackFrame, frame, cv::Size(_width / 2, _height / 2), _width / 2.0, 0, cv::INTER_LINEAR);
    }
    else if (_index > _frames.size() - 1)
    {
        // show last frame if index is higher than the number of frames
        cv::resize(_frames[_frames.size() - 1], frame, cv::Size(_width / 2, _height / 2), _width / 2.0, 0, cv::INTER_LINEAR);
    }
    else
    {
        cv::resize(_frames[_index], frame, cv::Size(_width / 2, _height / 2), _width / 2.0, 0, cv::INTER_LINEAR);
    }

    // load next frame if not in pause
    if (_paused == false)
    {
        _index += 1;
    }

    // convert to rgba because opencv stores it as bgra
    cv::cvtColor(frame, frame, cv::COLOR_BGRA2RGBA);

    // convert to pixmap for better display (cpu)
    QPixmap pixmap = QPixmap::fromImage(QImage(frame.data, frame.cols, frame.rows, frame.step, QImage::Format_RGBA8888));

    // update the currently shown image
    _imageLabel.setPixmap(pixmap);
}

int LiveWindow::run()
{
    return _app.exec();
}

void LiveWindow::goToLabel(const std::string &label)
{
    auto it = _labels.find(label);

    if (it != _labels.end())
    {
        _index = it->second;
        _currentLabel = label;
    }
}

void LiveWindow::addLabel(const std::string &label, std::size_t index)
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

void LiveWindow::removeLabel(const std::string &label)
{
    _labelsByVal.erase(_labels[label]);
    _labels.erase(label);
}

void LiveWindow::addFrames(const std::vector<cv::Mat> &frames)
{
    for (auto &i : frames)
    {
        addFrame(i);
    }
}

void LiveWindow::addFrame(const cv::Mat &frameToCopy)
{
    cv::Mat frame = _defaultBlackFrame.clone();

    // crop size
    int cropWidth = std::min(frameToCopy.cols, frame.cols);
    int cropHeight = std::min(frameToCopy.rows, frame.rows);

    // region of interest
    cv::Rect roi(0, 0, cropWidth, cropHeight);

    // copy the channels
    cv::Mat formattedFrame;
    cv::cvtColor(frameToCopy, formattedFrame, cv::COLOR_BGR2BGRA);

    // resize the frame
    formattedFrame(roi).copyTo(frame(roi));

    // add the resized frame
    _frames.push_back(frame);
}

void LiveWindow::pause()
{
    _paused = !_paused;
    std::cout << std::format("Timeline {} at frame '{}'.", _paused ? "paused" : "unpaused", _index) << std::endl;
}

void LiveWindow::stop()
{
    _running = false;
    QApplication::quit();
}

void LiveWindow::goToFirstFrame()
{
    goToLabel(_labelsByVal[0]);
    std::cout << std::format("Current Label set to '{}' at frame '0'.", _currentLabel) << std::endl;
}

void LiveWindow::goToLastFrame()
{
    goToLabel(std::prev(_labelsByVal.end())->second);
    std::cout << std::format("Current Label set to '{}' at frame '{}'.", _currentLabel, _index) << std::endl;
}

void LiveWindow::goToPreviousLabel()
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

void LiveWindow::goToNextLabel()
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
