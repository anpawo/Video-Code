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

#define bind(x) ([this]() { this->x(); })

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

    enum InputType {
        ImageTy,
        VideoTy,
    };

    /**
     * @ load an input into the env
     */
    void loadInput(std::string &&envName, std::string &&inputName, InputType inputTy);

    /**
     * @ get the frames of an input from the env
     */
    const std::vector<cv::Mat> &getInputFrames(std::string &&input);

    /**
     * @ get the frames of an input from the env
     */
    const std::unique_ptr<_IInput> &getInput(std::string &&input);

    /**************************************/
    /*** Below are the mapped functions ***/
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
    std::map<std::string, std::unique_ptr<_IInput>> _env{};

    /**
     * @ supported commands.
     */
    std::map<int, std::function<void()>> _commands{};

    /**
     * @ timeline unpaused.
     */
    bool _paused{false};

    /**
     * @ timeline running.
     */
    bool _running{true};

    /**
     * @ instructions of the input file
     */
    json::array_t _insts{};
};
