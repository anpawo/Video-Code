/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** LiveWindow
*/

#pragma once

#include <cstddef>
#include <functional>
#include <map>
#include <memory>
#include <nlohmann/json.hpp>
#include <opencv2/core/mat.hpp>
#include <string>
#include <vector>

#include "input/_IInput.hpp"

#define bindCmd(x) ([this]() { this->x(); })
#define bindInst(x) ([this](const json::array_t &args) { return this->x(args); })

using json = nlohmann::json;

class LiveWindow {
public:

    LiveWindow(int width, int height, std::string &&_sourceFile = "video.py");
    ~LiveWindow();

    /**
     * @ run the program
     */
    void run();

    /**
     * @ set the index of the timeline
     */
    void setIndex(std::size_t index);

    /**
     * @ set the index of the timeline to a label
     */
    void setIndex(const std::string &label);

    /**
     * @ get the current index
     */
    std::size_t getIndex() const;

    /**
     * @ find the label currently playing
     */
    const std::string &getLabel() const;

    /**
     * @ get all labels
     */
    const std::map<std::string, std::size_t> &getLabels() const;
    const std::map<std::size_t, std::string> &getLabelsByVal() const;

    /**
     * @ remove label
     */
    void removeLabel(const std::string &index);

    /**
     * @ add a label
     */
    void addLabel(const std::string &label, std::size_t index);

    /**
     * @ add a frame to the timeline. may crop it if needed.
     */
    void addFrame(const cv::Mat &frame);
    void addFrames(const std::vector<cv::Mat> &frames);

    /**
     * @ load an image into the env
     */
    void loadImage(std::string &&envName, std::string &&inputName);

    /**
     * @ load a video into the env
     */
    void loadVideo(std::string &&envName, std::string &&inputName);

    /**
     * @ get the frames of an input from the env
     */
    const std::vector<cv::Mat> &getInputFrames(std::string &&input);

    /**
     * @ get the frames of an input from the env
     */
    const std::shared_ptr<_IInput> &getInput(std::string &&input);

    /**
     * @ remove old env
     */
    void removeOld();

    /**
     * @ execute the instruction
     */
    std::shared_ptr<_IInput> executeInst(const json::array_t &inst);
    void executeInsts(const json::array_t &insts);

    /**
     * @ declare a variable in the env
     */
    void assign(const std::string &name, const json::array_t &inst);

    /**************************************/
    /*** Below are the mapped commands ***/
    /**************************************/

    /**
     * @ restart the timeline
     */
    void restart();

    /**
     * @ pause the timeline
     */
    void pause();

    /**
     * @ unpause the timeline
     */
    void unpause();

    /**
     * @ stop the window
     */
    void stop();

    /**
     * @ jump to previous label
     */
    void previousLabel();

    /**
     * @ jump to next label
     */
    void nextLabel();

    /**
     * @ reload input file
     */
    void reloadSourceFile();

    /*****************************************/
    /*** Below are the mapped instructions ***/
    /*****************************************/

    /**
     * @ load a variable from the env
     */
    std::shared_ptr<_IInput> load(const json::array_t &args);

    /**
     * @ call a builtin function
     */
    std::shared_ptr<_IInput> call(const json::array_t &args);

    /**
     * @ add the frames of an input to the timeline
     */
    std::shared_ptr<_IInput> add(const json::array_t &args);

    /**
     * @ create a new label
     */
    std::shared_ptr<_IInput> label(const json::array_t &args);

    /**
     * @ import an image
     */
    std::shared_ptr<_IInput> image(const json::array_t &args);

    /**
     * @ import a video
     */
    std::shared_ptr<_IInput> video(const json::array_t &args);

    /**
     * @ repeat an input n times and returns it
     */
    std::shared_ptr<_IInput> repeat(const json::array_t &args);

    /**
     * @ take a slice out of an input
     */
    std::shared_ptr<_IInput> subscript(const json::array_t &args);

private:

    /**
     * @ size of the window.
     */
    const int _width{1920};
    const int _height{1080};

    /**
     * @ source file
     */
    const std::string _sourceFile;

    /**
     * @ default window name
     */
    const std::string _defaultWindowName{"default"};

    /**
     * @ default frame.
     * - black frame for empty timelines
     */
    const cv::Mat _defaultBlackFrame;

    /**
     * @ current index of the timeline.
     */
    std::size_t _index{0};

    /**
     * @ all frames of the timeline.
     */
    std::vector<cv::Mat> _frames{};

    /**
     * @ labels.
     * - used to play some part of the video
     */
    std::map<std::string, std::size_t> _labels{{"__start", 0}};
    std::map<std::size_t, std::string> _labelsByVal{{0, "__start"}};

    /**
     * @ label currently playing
     */
    std::string _currentLabel{"__start"};

    /**
     * @ env.
     * - currently loaded image and video
     */
    std::map<std::string, std::shared_ptr<_IInput>> _env{};

    /**
     * @ supported commands.
     */
    // clang-format off
    const std::map<int, std::function<void()>> _commands{
        {'r', bindCmd(restart)},
        {'a', bindCmd(pause)},
        {'e', bindCmd(unpause)},
        { 81, bindCmd(previousLabel)},    // left
        { 83, bindCmd(nextLabel)},        // right
        { 27, bindCmd(stop)},             // escape
        { 32, bindCmd(reloadSourceFile)}, // space
    };
    // clang-format on

    /**
     * @ supported instructions.
     */
    // clang-format off
    const std::map<std::string, std::function<std::shared_ptr<_IInput>(const json::array_t &args)>> _instructions{
        /***    Main Instructions    ***/
        { "load",      bindInst(load) },
        { "Call",      bindInst(call) },
        { "add",       bindInst(add) },
        { "label",     bindInst(label) },
        /***    Load Instructions    ***/
        { "image",     bindInst(image) },
        { "video",     bindInst(video) },
        /***        Routines         ***/
        { "repeat",    bindInst(repeat) },
        { "subscript", bindInst(subscript) },
    };
    // clang-format on

    /**
     * @ timeline unpaused.
     */
    bool _paused{true};

    /**
     * @ timeline running.
     */
    bool _running{true};

    /**
     * @ instructions of the input file
     */
    json::array_t _insts{};
};

// TODO: should cache the loaded images/video (with a time modification?)
