/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** LiveWindow
*/

#include "vm/VideoCode.hpp"

#include <fmt/core.h>
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
    , _defaultBlackFrame(cv::Mat(height, width, CV_8UC4).setTo(cv::Scalar(0, 0, 0, 0)))
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
    _register.clear();
    _keptInputs.clear();

    std::string serializedScene;

    try
    {
        serializedScene = python::API::call<std::string>("Serialize", "serializeScene", _sourceFile);
    } catch (const Error &e)
    {
        std::cout << "Invalid source file, could not parse the instructions." << std::endl;
        return;
    }

    json::array_t stack = json::parse(serializedScene);

    for (const auto &i : stack)
    {
        std::cout << i << std::endl;
    }

    _stack = std::move(stack);

    executeStack();

    std::cout << _labels << std::endl;
    std::cout << _labelsByVal << std::endl;
}

void VideoCode::executeStack()
{
    for (const auto &i : _stack)
    {
        if (i["action"] == "Create")
        {
            ///< {"action": 'Create', "type": Image, **kwargs}
            _register.newInput(i["type"], i);
        }
        else if (i["action"] == "Add")
        {
            ///< {"action": 'Add', "input": 0}
            addFrames(_register[i["input"]]);
        }
        else if (i["action"] == "Apply")
        {
            ///< {"action": 'Apply', "input": 0, "transformation": 'overlay', "fg": 1}

            VC_LOG_DEBUG("transformation: " << i["transformation"] << ": " << i["input"]);

            transformation::map.at(i["transformation"])(_register[i["input"]], _register, i["args"]);
        }
        else if (i["action"] == "Wait")
        {
            for (size_t n = 0; n < i["n"]; n++)
            {
                if (_frames.empty())
                {
                    _frames.push_back(_defaultBlackFrame.clone());
                }
                else
                {
                    _frames.push_back(_frames.back().clone());
                }
            }
        }
        else if (i["action"] == "Keep")
        {
            _keptInputs.push_back(i["input"]);
        }
        else if (i["action"] == "Drop")
        {
            _keptInputs.erase(std::remove_if(_keptInputs.begin(), _keptInputs.end(), [](int i) { return i == i["input"]; }));
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
    for (const Frame &f : *frames)
    {
        addFrame(f);
    }
}

static void overlayKeptInput(cv::Mat &background, const Frame &frame)
{
    const auto &meta = frame._meta;
    const auto &overlay = frame._mat;

    // Calculate the source rectangle
    int srcX = std::max(0, -meta.x);
    int srcY = std::max(0, -meta.y);
    int srcW = std::min(overlay.cols - srcX, background.cols);
    int srcH = std::min(overlay.rows - srcY, background.rows);

    // Calculate the destination rectangle
    int dstX = std::max(0, meta.x);
    int dstY = std::max(0, meta.y);
    int dstW = srcW;
    int dstH = srcH;

    // Ensure the destination rectangle is within the frame bounds
    dstW = std::min(dstW, background.cols - dstX);
    dstH = std::min(dstH, background.rows - dstY);

    // Adjust the source rectangle if the destination rectangle was reduced
    srcW = dstW;
    srcH = dstH;

    // Define the source and destination regions
    cv::Rect src(srcX, srcY, srcW, srcH);
    cv::Rect dst(dstX, dstY, dstW, dstH);

    // Only copy if we have valid regions
    if (src.width > 0 && src.height > 0 && dst.width > 0 && dst.height > 0)
    {
        for (int y = 0; y < src.height; y++)
        {
            for (int x = 0; x < src.width; x++)
            {
                const cv::Vec4b &bgPixel = background.at<cv::Vec4b>(y + dst.y, x + dst.x);
                const cv::Vec4b &ovPixel = overlay.at<cv::Vec4b>(y + src.y, x + src.x);

                // if (ovPixel[0] == 0 && ovPixel[1] == 0 && ovPixel[1] == 0 && ovPixel[3] != 0)
                // {
                //     // std::cout << "x:" << x << std::endl;
                //     // std::cout << "y:" << y << std::endl;
                //     // std::cout << "alpha:" << (int)ovPixel[3] << std::endl;
                //     continue;
                // }

                const float alphaBg = bgPixel[3] / 255.0f;
                const float alphaOv = ovPixel[3] / 255.0f;

                cv::Vec4b tmp;
                for (int i = 0; i < 3; i++)
                {
                    tmp[i] = static_cast<uchar>(
                        (ovPixel[i] * alphaOv + bgPixel[i] * (1.0f - alphaOv))
                    );
                }
                tmp[3] = (alphaBg + alphaOv * (1.0f - alphaBg)) * 255.0f;

                background.at<cv::Vec4b>(y + dst.y, x + dst.x) = tmp;
            }
        }
    }
}

void VideoCode::addFrame(const Frame &frame)
{
    cv::Mat finalFrame = _defaultBlackFrame.clone();

    for (const auto &i : _keptInputs)
    {
        overlayKeptInput(finalFrame, _register[i]->back());
    }
    overlayKeptInput(finalFrame, frame);

    _frames.push_back(finalFrame);
}

void VideoCode::pause()
{
    _paused = !_paused;
    std::cout << fmt::format("Timeline {} at frame '{}'.", _paused ? "paused" : "unpaused", _index) << std::endl;
}

void VideoCode::stop()
{
    _running = false;
    QApplication::quit();
}

void VideoCode::goToFirstFrame()
{
    goToLabel(_labelsByVal[0]);
    std::cout << fmt::format("Current Label set to '{}' at frame '0'.", _currentLabel) << std::endl;
}

void VideoCode::goToLastFrame()
{
    goToLabel(std::prev(_labelsByVal.end())->second);
    std::cout << fmt::format("Current Label set to '{}' at frame '{}'.", _currentLabel, _index) << std::endl;
}

void VideoCode::goToPreviousLabel()
{
    if (_labels[_currentLabel] == 0)
    {
        goToLabel(_currentLabel);
        std::cout << fmt::format("Timeline set to the start of the current label '{}', at frame '{}'.", _currentLabel, _index) << std::endl;
    }
    else
    {
        goToLabel(std::prev(_labelsByVal.find(_labels[_currentLabel]))->second);
        std::cout << fmt::format("Timeline set to the previous label '{}', at frame '{}'.", _currentLabel, _index) << std::endl;
    }
}

void VideoCode::goToNextLabel()
{
    auto next = std::next(_labelsByVal.find(_labels[_currentLabel]));

    if (next == _labelsByVal.end())
    {
        _index = _frames.size() - 1;
        std::cout << fmt::format("Timeline set to last index, '{}'", _index) << std::endl;
    }
    else
    {
        goToLabel(next->second);
        std::cout << fmt::format("Timeline set to the next label '{}', at frame '{}'.", _currentLabel, _index) << std::endl;
    }
}
