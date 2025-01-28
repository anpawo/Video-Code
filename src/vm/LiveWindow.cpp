/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** LiveWindow
*/

#include "vm/LiveWindow.hpp"

#include <unistd.h>

#include <format>
#include <functional>
#include <iostream>
#include <memory>
#include <opencv2/core/mat.hpp>
#include <opencv2/highgui.hpp>
#include <opencv2/imgproc.hpp>
#include <string>

#include "input/Image.hpp"
#include "input/List.hpp"
#include "input/Slice.hpp"
#include "input/Video.hpp"
#include "input/_IInput.hpp"
#include "python/API.hpp"
#include "utils/Exception.hpp"
#include "utils/Map.hpp"

LiveWindow::LiveWindow(int width, int height, std::string &&sourceFile)
    : _width(width)
    , _height(height)
    , _sourceFile(sourceFile)
    , _defaultBlackFrame(cv::Mat::zeros(height, width, CV_8UC4))
{
    // all below is for testing before the parsing works
    // addLabel("1_Label_30", 30);
    // addLabel("2_Label_45", 45);
    // addLabel("3_Label_60", 60);
    // addLabel("4_Label_75", 75);
    // addLabel("5_Label_90", 90);
    // addLabel("6_Label_120", 120);
    // addLabel("7_Label_150", 150);

    // std::cout << "labels" << std::endl;
    // std::cout << _labels << std::endl;

    // loadImage("ecs", "video/ecs.png");
    // loadImage("icon", "video/icon.png");
    // loadVideo("me", "video/me.mp4");

    // addFrames(getInputFrames("ecs"));
    // addFrames(getInputFrames("me"));

    reloadSourceFile();
}

LiveWindow::~LiveWindow()
{
    cv::destroyAllWindows();
}

void LiveWindow::run()
{
    int key;

    while (_running) {
        // display the current frame
        {
            // resize the frames to fit the size of the window
            cv::Mat resizedFrame;

            if (_frames.size() == 0) {
                // show black background if no frames are loaded
                cv::resize(_defaultBlackFrame, resizedFrame, cv::Size(_width / 2, _height / 2), _width / 2.0, 0, cv::INTER_LINEAR);
            } else if (_index > _frames.size() - 1) {
                // show last frame if index is higher than the number of frames
                cv::resize(_frames[_frames.size() - 1], resizedFrame, cv::Size(_width / 2, _height / 2), _width / 2.0, 0, cv::INTER_LINEAR);
            } else {
                cv::resize(_frames[_index], resizedFrame, cv::Size(_width / 2, _height / 2), _width / 2.0, 0, cv::INTER_LINEAR);

                // load next frame if not in pause
                if (_paused == false) {
                    _index += 1;
                }
            }

            // show the frame
            cv::imshow(_defaultWindowName, resizedFrame);
            cv::moveWindow(_defaultWindowName, _width / 2, 0);
        }

        // get the input and react
        {

            key = cv::waitKey(24);

            auto cmd = _commands.find(key);
            if (cmd != _commands.end()) {
                cmd->second();
            }
        }
    }
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
    std::cout << "Timeline restarted at frame 0." << std::endl;
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

    // for (std::size_t i = 0; i < newInsts.size(); i++) {
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
            assign(inst[1], inst[2]);
        } else {
            executeInst(inst);
        }
    }
}

std::shared_ptr<_IInput> LiveWindow::executeInst(const json::array_t &inst)
{
    return _instructions.at(inst[0])(inst);
}

void LiveWindow::assign(const std::string &name, const json::array_t &inst)
{
    _env[name] = executeInst(inst);
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

std::shared_ptr<_IInput> LiveWindow::label(const json::array_t &args)
{
    addLabel(args[0], _frames.size()); // TODO: not sure
    return nullptr;
}

std::shared_ptr<_IInput> LiveWindow::image(const json::array_t &args)
{
    return std::make_unique<Image>(std::forward<std::string>(args[0]));
}

std::shared_ptr<_IInput> LiveWindow::video(const json::array_t &args)
{
    return std::make_unique<Video>(std::forward<std::string>(args[0]));
}

std::shared_ptr<_IInput> LiveWindow::repeat(const json::array_t &args)
{
    return std::make_unique<List>(executeInst(args[0]), args[1]);
}

std::shared_ptr<_IInput> LiveWindow::subscript(const json::array_t &args)
{
    return std::make_unique<Slice>(executeInst(args[0]), args[1], args[2]);
}

std::shared_ptr<_IInput> LiveWindow::apply(const json::array_t &args)
{
    const std::shared_ptr<_IInput> input = executeInst(args[0]);

    return _transformations.at(args[1][1])(input, args[1][2]);
}

std::shared_ptr<_IInput> LiveWindow::grayscale(std::shared_ptr<_IInput> input, [[maybe_unused]] const json::array_t &args)
{
    std::shared_ptr<_IInput> out = std::make_shared<List>(input, input->getFrames().size());

    for (auto &m : out->getFramesForTransformation()) {
        cv::cvtColor(m, m, cv::COLOR_BGR2GRAY);
    }

    return out;
}

std::shared_ptr<_IInput> LiveWindow::fade([[maybe_unused]] std::shared_ptr<_IInput> input, const json::array_t &args)
{
    const std::shared_ptr<_IInput> frames = executeInst(args[0]); // TODO:

    // return std::make_unique<Slice>(executeInst(args[0]), args[1], args[2]);
    return {};
}
