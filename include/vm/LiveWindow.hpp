/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** LiveWindow
*/

#pragma once

#include <qapplication.h>
#include <qwidget.h>

#include <cstddef>
#include <functional>
#include <map>
#include <memory>
#include <nlohmann/json.hpp>
#include <opencv2/core/mat.hpp>
#include <string>
#include <vector>

#include "input/_IInput.hpp"
#include "qboxlayout.h"
#include "qlabel.h"
#include "qnamespace.h"
#include "qtimer.h"
#include "vm/WindowEvent.hpp"

#define bindCmd(x) ([this]() { this->x(); })
#define bindInst(x) ([this](const json::array_t &args) { return this->x(args); })
#define bindTsf(x) ([this](std::shared_ptr<_IInput> input, const json::array_t &args) { return this->x(input, args); })

using json = nlohmann::json;

class LiveWindow {
public:

    LiveWindow(int &argc, char **argv, int width, int height, std::string &&_sourceFile = "video.py");
    ~LiveWindow();

    /**
     * @ run the program
     */
    int run();

    /**
     * @ update the currently showed frame
     */
    void updateFrame();

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
     * @ declare or update a variable in the env
     */
    void assign(const json::array_t &args);

    /**
     * @ create a new label
     */
    void label(const std::string &name);

    /**************************************/
    /*** Below are the mapped events ***/
    /**************************************/

    /**
     * @ restart the timeline
     */
    void firstFrame();

    /**
     * @ load the last frame of the timeline
     */
    void lastFrame();

    /**
     * @ pause the timeline
     */
    void pause();

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
     * @ copy an input and returns it
     */
    std::shared_ptr<_IInput> copy(const json::array_t &args);

    /**
     * @ concat 2 inputs and returns the result
     */
    std::shared_ptr<_IInput> concat(const json::array_t &args);

    /**
     * @ take a slice out of an input
     */
    std::shared_ptr<_IInput> subscript(const json::array_t &args);

    /**
     * @ apply a transformation to an input
     */
    std::shared_ptr<_IInput> apply(const json::array_t &args);

    /*****************************************/
    /***   Below are the transformations   ***/
    /*****************************************/

    /**
     * @ fade in or out from a side for a certain number of frame or sec
     */
    std::shared_ptr<_IInput> fadeIn(std::shared_ptr<_IInput> input, const json::array_t &args);

    /**
     * @ grayscale an image
     */
    std::shared_ptr<_IInput> grayscale(std::shared_ptr<_IInput> input, const json::array_t &args);

private:

    /**
     * @ video frame rate.
     */
    const int _frameRate{24};

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
     * @ qt app
     */
    QApplication _app;

    /**
     * @ qt window
     */
    WindowEvent _window;

    /**
     * @ label linking the image and the label.
     */
    QLabel _imageLabel;

    /**
     * @ layout linking the label and the window.
     */
    QVBoxLayout _imageLayout;

    /**
     * @ loop updating the current frame
     */
    QTimer _timer;

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
    const std::map<int, std::function<void()>> _events{
        {Qt::Key_Down,      bindCmd(firstFrame)},
        {Qt::Key_Up,        bindCmd(lastFrame)},
        {Qt::Key_Left,      bindCmd(previousLabel)},   
        {Qt::Key_Right,     bindCmd(nextLabel)},       
        {Qt::Key_Space,     bindCmd(pause)},
        {Qt::Key_R,         bindCmd(reloadSourceFile)},
        {Qt::Key_Escape,    bindCmd(stop)},            
    };
    // clang-format on

    /**
     * @ supported instructions.
     */
    // clang-format off
    const std::map<std::string, std::function<std::shared_ptr<_IInput>(const json::array_t &args)>> _instructions{
        /***    Main Instructions    ***/
        { "Call",      bindInst(call) },
        { "load",      bindInst(load) },
        { "add",       bindInst(add) },
        /***    Load Instructions    ***/
        { "image",     bindInst(image) },
        { "video",     bindInst(video) },
        /***        Routines         ***/
        { "repeat",    bindInst(repeat) },
        { "copy",      bindInst(copy) },
        { "concat",    bindInst(concat) },
        { "subscript", bindInst(subscript) },
        { "apply",     bindInst(apply) },
    };
    // clang-format on

    // clang-format off
    const std::map<std::string, std::function<std::shared_ptr<_IInput>(std::shared_ptr<_IInput> input, const json::array_t &args)>> _transformations
    {
        /***     Transformations     ***/
        {"grayscale",   bindTsf(grayscale)},
        {"fadeIn",      bindTsf(fadeIn)},
        // {"fade",      bindTsf(scale)},
        // {"fade",      bindTsf(rotate)},
        // {"fade",      bindTsf(translate)},
        // {"fade",      bindTsf(flip/reflection)},
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
