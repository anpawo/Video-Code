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

void LiveWindow::setIndex(std::size_t index)
{
    _index = index;
    _currentLabel = _labelsByVal[index];
}

void LiveWindow::setIndex(const std::string &label)
{
    auto it = _labels.find(label);

    if (it != _labels.end()) {
        setIndex(it->second);
        _currentLabel = label;
    }
}

std::size_t LiveWindow::getIndex() const
{
    return _index;
}

const std::string &LiveWindow::getLabel() const
{
    return _currentLabel;
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
    return _env[input]->getFrames();
}

const std::shared_ptr<_IInput> &LiveWindow::getInput(std::string &&input)
{
    return _env[input];
}

void LiveWindow::restart()
{
    setIndex(0);
    std::cout << "Timeline restarted at frame '0'." << std::endl;
}

void LiveWindow::pause()
{
    _paused = true;
    std::cout << std::format("Timeline paused at frame '{}'.", getIndex()) << std::endl;
}

void LiveWindow::unpause()
{
    _paused = false;
    std::cout << std::format("Timeline unpaused at frame '{}'.", getIndex()) << std::endl;
}

void LiveWindow::stop()
{
    _running = false;
    QApplication::quit();
}

void LiveWindow::previousLabel()
{
    if (getLabel() == "__start") {
        setIndex(getLabel());
        std::cout << std::format("Timeline set to the start of the current label '{}', at frame '{}'.", getLabel(), getIndex()) << std::endl;
    } else {
        setIndex((--(getLabelsByVal().find(getLabels().at(getLabel()))))->second);
        std::cout << std::format("Timeline set to the previous label '{}', at frame '{}'.", getLabel(), getIndex()) << std::endl;
    }
}

void LiveWindow::nextLabel()
{
    auto upperBound = getLabelsByVal().upper_bound(getLabels().at(getLabel()));

    if (upperBound == getLabelsByVal().end()) {
        std::cout << std::format("The Timeline is currently at the last label, '{}'", getLabel()) << std::endl;
    } else {
        setIndex(upperBound->first);
        std::cout << std::format("Timeline set to the next label '{}', at frame '{}'.", getLabel(), getIndex()) << std::endl;
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
}

void LiveWindow::removeOld()
{
    _env.clear();

    _labels = {{"__start", 0}};
    _labelsByVal = {{0, "__start"}};
    _currentLabel = "__start";

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
    addFrames(executeInst(args[0])->getFrames());
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

std::shared_ptr<_IInput> LiveWindow::apply(const json::array_t &args) // TODO: check if list or transformation or just one
{
    const std::shared_ptr<_IInput> input = executeInst(args[0]);

    return _transformations.at(args[1][1])(input, args[1][2]);
}

std::shared_ptr<_IInput> LiveWindow::grayscale(std::shared_ptr<_IInput> input, [[maybe_unused]] const json::array_t &args)
{
    if (input->getFrames().empty() || input->getFrames()[0].channels() == 1) {
        return input;
    }

    for (auto &m : input->getFramesForTransformation()) {
        cv::cvtColor(m, m, cv::COLOR_BGR2GRAY); // TODO: should be deduced or does it needs it ?
    }

    return input;
}

std::shared_ptr<_IInput> LiveWindow::fade(std::shared_ptr<_IInput> input, [[maybe_unused]] const json::array_t &args)
{
    std::size_t nbFrames = input->getFrames().size();

    for (std::size_t i = 0; i < nbFrames; i++) {
        auto &m = input->getFramesForTransformation()[i];
        m.col(i).forEach<cv::Vec4b>([](cv::Vec4b &pixel, const int *) {
            pixel[3] = 0;
        });
    }

    return input;
}
