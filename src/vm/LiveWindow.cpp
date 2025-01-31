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
#include <format>
#include <iostream>
#include <memory>
#include <opencv2/core/mat.hpp>
#include <opencv2/core/matx.hpp>
#include <opencv2/highgui.hpp>
#include <opencv2/imgproc.hpp>
#include <string>

#include "input/Image.hpp"
#include "input/List.hpp"
#include "input/Slice.hpp"
#include "input/Video.hpp"
#include "input/_IInput.hpp"
#include "opencv2/core.hpp"
#include "opencv2/core/types.hpp"
#include "python/API.hpp"
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
    _timer.start(24);

    // QPixmap image("video/icon.png");

    // QLabel *imageLabel = new QLabel();
    // imageLabel->setPixmap(image);

    // QVBoxLayout layout;
    // layout.addWidget(imageLabel);
    // _window.setLayout(&layout);
    // image = QPixmap("video/ecs.png");
    // imageLabel->setPixmap(image);

    // _app.add

    reloadSourceFile();

    // QObject::connect();
}

LiveWindow::~LiveWindow()
{
    cv::destroyAllWindows();
}

void LiveWindow::updateFrame()
{
    cv::Mat frame;

    if (_frames.size() == 0) {
        // show black background if no frames are loaded
        cv::resize(_defaultBlackFrame, frame, cv::Size(_width / 2, _height / 2), _width / 2.0, 0, cv::INTER_LINEAR);
    } else if (_index > _frames.size() - 1) {
        // show last frame if index is higher than the number of frames
        cv::resize(_frames[_frames.size() - 1], frame, cv::Size(_width / 2, _height / 2), _width / 2.0, 0, cv::INTER_LINEAR);
    } else {
        cv::resize(_frames[_index], frame, cv::Size(_width / 2, _height / 2), _width / 2.0, 0, cv::INTER_LINEAR);
    }

    // load next frame if not in pause
    if (_paused == false) {
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

    if (it != _labels.end()) {
        _index = it->second;
        _currentLabel = label;
    }
}

const std::map<std::string, std::size_t> &LiveWindow::getLabels() const
{
    return _labels;
}

const std::map<std::size_t, std::string> &LiveWindow::getLabelsByVal() const
{
    return _labelsByVal;
}

void LiveWindow::removeLabel(const std::string &label)
{
    _labelsByVal.erase(_labels[label]);
    _labels.erase(label);
}

void LiveWindow::addLabel(const std::string &label, std::size_t index)
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

void LiveWindow::addFrames(const std::vector<cv::Mat> &frames)
{
    for (auto &i : frames) {
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

void LiveWindow::loadImage(std::string &&envName, std::string &&inputName)
{
    _env[envName] = std::make_unique<Image>(std::forward<std::string>(inputName));
}

void LiveWindow::loadVideo(std::string &&envName, std::string &&inputName)
{
    _env[envName] = std::make_unique<Video>(std::forward<std::string>(inputName));
}

const std::vector<cv::Mat> &LiveWindow::getInputFrames(std::string &&input)
{
    return _env[input]->cgetFrames();
}

const std::shared_ptr<_IInput> &LiveWindow::getInput(std::string &&input)
{
    return _env[input];
}

void LiveWindow::firstFrame()
{
    _index = 0;
    _currentLabel = _labelsByVal[0];
    std::cout << std::format("Current Label set to '{}' at frame '0'.", _currentLabel) << std::endl;
}

void LiveWindow::lastFrame()
{
    _index = _frames.size() - 1;
    _currentLabel = std::prev(_labelsByVal.end())->second;
    std::cout << std::format("Current Label set to '{}' at frame '{}'.", _currentLabel, _index) << std::endl;
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

void LiveWindow::previousLabel()
{
    if (_labels[_currentLabel] == 0) {
        goToLabel(_currentLabel);
        std::cout << std::format("Timeline set to the start of the current label '{}', at frame '{}'.", _currentLabel, _index) << std::endl;
    } else {
        goToLabel(std::prev(_labels.find(_currentLabel))->first);
        std::cout << std::format("Timeline set to the previous label '{}', at frame '{}'.", _currentLabel, _index) << std::endl;
    }
}

void LiveWindow::nextLabel()
{
    auto upperBound = getLabelsByVal().upper_bound(_labels[_currentLabel]);

    if (upperBound == getLabelsByVal().end()) {
        std::cout << std::format("The Timeline is currently at the last label, '{}'", _currentLabel) << std::endl;
    } else {
        goToLabel(upperBound->second);
        std::cout << std::format("Timeline set to the next label '{}', at frame '{}'.", _currentLabel, _index) << std::endl;
    }
}

void LiveWindow::reloadSourceFile()
{
    std::string serializedInsts;

    try {
        serializedInsts = python::API::call<std::string>("serialise", "toJson", _sourceFile);
    } catch (const Error &e) {
        std::cout << "Invalid source file, could not parse the instructions." << std::endl;
        return;
    }

    json::array_t newInsts = json::parse(serializedInsts);

    if (newInsts == _insts) {
        return;
    }

    // for (std::size_t i = 0; i < newInsts.size(); i++) { // TODO: cache
    //     if (newInsts[i] == _insts[i]) {
    //         continue;
    //     }
    //     executeInsts(const json::array_t &insts)
    //     break;
    // }

    removeOld();
    executeInsts(newInsts);
    std::cout << newInsts << std::endl;
    _insts = newInsts;
    std::cout << _labels << std::endl;
    std::cout << _labelsByVal << std::endl;
}

void LiveWindow::removeOld()
{
    _env.clear();

    _labels = {{_initialLabel, 0}};
    _labelsByVal = {{0, _initialLabel}};
    _currentLabel = _initialLabel;

    _frames.clear();
}

void LiveWindow::executeInsts(const json::array_t &insts)
{
    for (const auto &i : insts) {
        const json::array_t &inst = i;
        if (inst[0] == "Assign") {
            assign(inst);
        } else if (inst[0] == "Label") {
            label(inst[1]);
        } else {
            executeInst(inst); // Is a Call but Calls can be chained.
        }
    }
}

void LiveWindow::assign(const json::array_t &args)
{
    _env[args[1]] = executeInst(args[2]);
}

void LiveWindow::label(const std::string &name)
{
    addLabel(name, _frames.size());
}

std::shared_ptr<_IInput> LiveWindow::executeInst(const json::array_t &inst)
{
    return _instructions.at(inst[0])(inst);
}

std::shared_ptr<_IInput> LiveWindow::load(const json::array_t &args)
{
    return _env.at(args[0]);
}

std::shared_ptr<_IInput> LiveWindow::call(const json::array_t &args)
{
    return _instructions.at(args[1])(args[2]);
}

std::shared_ptr<_IInput> LiveWindow::add(const json::array_t &args)
{
    addFrames(executeInst(args[0])->cgetFrames());
    return nullptr;
}

std::shared_ptr<_IInput> LiveWindow::image(const json::array_t &args)
{
    return std::make_unique<Image>(args[0]);
}

std::shared_ptr<_IInput> LiveWindow::video(const json::array_t &args)
{
    return std::make_unique<Video>(args[0]);
}

std::shared_ptr<_IInput> LiveWindow::repeat(const json::array_t &args)
{
    return std::make_unique<List>(executeInst(args[0]), args[1]);
}

std::shared_ptr<_IInput> LiveWindow::copy(const json::array_t &args)
{
    return std::make_unique<List>(executeInst(args[0]));
}

std::shared_ptr<_IInput> LiveWindow::concat(const json::array_t &args)
{
    std::shared_ptr<_IInput> head = executeInst(args[0]);
    std::shared_ptr<_IInput> tail = executeInst(args[1]);

    head->concat(tail);

    return head;
}

std::shared_ptr<_IInput> LiveWindow::subscript(const json::array_t &args)
{
    return std::make_unique<Slice>(executeInst(args[0]), args[1], args[2]);
}

std::shared_ptr<_IInput> LiveWindow::apply(const json::array_t &args)
{
    std::shared_ptr<_IInput> input = executeInst(args[0]);

    for (auto it = args.begin() + 1; it != args.end(); it++) {
        input = _transformations.at((*it)[1])(input, (*it)[2]);
    }

    return input;
}

std::shared_ptr<_IInput> LiveWindow::grayscale(std::shared_ptr<_IInput> input, [[maybe_unused]] const json::array_t &args)
{
    if (input->cgetFrames().empty() || input->cgetFrames()[0].channels() == 1) {
        return input;
    }

    for (auto &m : input->getFrames()) {
        cv::cvtColor(m, m, cv::COLOR_BGR2GRAY); // TODO: should be deduced or does it needs it ?
    }

    return input;
}

std::shared_ptr<_IInput> LiveWindow::fadeIn(std::shared_ptr<_IInput> input, const json::array_t &args)
{
    int nbFrames = input->cgetFrames().size();
    std::string side = args[0];
    int duration = args[1];

    if (duration < 0) {
        duration += nbFrames + 1;
    }

    if (side == "LEFT") {

        for (int n = 0; n < nbFrames; n++) {
            ///< don't affect frames after duration
            if (n >= duration) {
                break;
            }

            // current frame
            auto &m = input->getFrames()[n];

            for (int i = 0; i < m.cols; i++) {
                float progress = i / static_cast<float>(m.cols) / 10;

                // We want to ensure the fade finishes when n == duration
                float mul = std::min(1.0f, static_cast<float>(n) / static_cast<float>(duration) + progress);

                m.col(m.cols - 1 - i).forEach<cv::Vec4b>([mul](cv::Vec4b &pixel, const int *) {
                    pixel[3] *= mul; ///< ensure that many tranformations can be done at the same time
                });
            }
        }
    } else if (side == "RIGHT") {

        for (int n = 0; n < nbFrames; n++) {
            ///< don't affect frames after duration
            if (n >= duration) {
                break;
            }

            // current frame
            auto &m = input->getFrames()[n];

            for (int i = 0; i < m.cols; i++) {
                float progress = i / static_cast<float>(m.cols) / 10;

                // We want to ensure the fade finishes when n == duration
                float mul = std::min(1.0f, static_cast<float>(n) / static_cast<float>(duration) + progress);

                m.col(i).forEach<cv::Vec4b>([mul](cv::Vec4b &pixel, const int *) {
                    pixel[3] *= mul; ///< ensure that many tranformations can be done at the same time
                });
            }
        }
    } else if (side == "DOWN") {
        for (int n = 0; n < nbFrames; n++) {
            ///< don't affect frames after duration
            if (n >= duration) {
                break;
            }

            // current frame
            auto &m = input->getFrames()[n];

            for (int i = 0; i < m.rows; i++) {
                float progress = i / static_cast<float>(m.rows) / 10;

                // We want to ensure the fade finishes when n == duration
                float mul = std::min(1.0f, static_cast<float>(n) / static_cast<float>(duration) + progress);

                m.row(i).forEach<cv::Vec4b>([mul](cv::Vec4b &pixel, const int *) {
                    pixel[3] *= mul; ///< ensure that many tranformations can be done at the same time
                });
            }
        }
    } else if (side == "UP") {
        for (int n = 0; n < nbFrames; n++) {
            ///< don't affect frames after duration
            if (n >= duration) {
                break;
            }

            // current frame
            auto &m = input->getFrames()[n];

            for (int i = 0; i < m.rows; i++) {
                float progress = i / static_cast<float>(m.rows) / 10;

                // We want to ensure the fade finishes when n == duration
                float mul = std::min(1.0f, static_cast<float>(n) / static_cast<float>(duration) + progress);

                m.row(m.rows - 1 - i).forEach<cv::Vec4b>([mul](cv::Vec4b &pixel, const int *) {
                    pixel[3] *= mul; ///< ensure that many tranformations can be done at the same time
                });
            }
        }
    } else if (side == "ALL") {
        for (int n = 0; n < nbFrames; n++) {
            ///< don't affect frames after duration
            if (n >= duration) {
                break;
            }

            // current frame
            auto &m = input->getFrames()[n];

            for (int i = 0; i < m.rows; i++) {
                // We want to ensure the fade finishes when n == duration
                float mul = std::min(1.0f, static_cast<float>(n) / static_cast<float>(duration));

                m.row(m.rows - 1 - i).forEach<cv::Vec4b>([mul](cv::Vec4b &pixel, const int *) {
                    pixel[3] *= mul; ///< ensure that many tranformations can be done at the same time
                });
            }
        }
    }

    return input;
}

std::shared_ptr<_IInput> LiveWindow::translate(std::shared_ptr<_IInput> input, const json::array_t &args)
{
    int x = args[0];
    int y = args[1];

    for (auto &m : input->getFrames()) {
        if (x < 0) {
            // rm col
            m = m.rowRange(-x, m.rows);
        } else if (x > 0) {
            // add col
            cv::vconcat(cv::Mat(x, m.cols, CV_8UC4).setTo(cv::Scalar(0, 0, 0, 255)), m, m);
        }
        if (y < 0) {
            // rm row
            m = m.colRange(-y, m.cols);
        } else if (y > 0) {
            // add row
            cv::hconcat(cv::Mat(m.rows, y, CV_8UC4).setTo(cv::Scalar(0, 0, 0, 255)), m, m);
        }
    }

    return input;
}
