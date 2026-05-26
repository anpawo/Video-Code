/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Core
*/

#include "core/Core.hpp"

#include <pybind11/embed.h>
#include <pybind11/stl.h>

#include <cstddef>
#include <format>
#include <iostream>
#include <memory>
#include <nlohmann/json.hpp>
#include <string>

using json = nlohmann::json;

#include "core/Config.hpp"
#include "input/AInput.hpp"
#include "input/IInput.hpp"
#include "input/InputFactory.hpp"
#include "input/media/Image.hpp"
// #include "input/media/Video.hpp"
#include "utils/Exception.hpp"
#include "utils/Logger.hpp"
#include "window/VulkanWidget.hpp"

VC::Core::Core(const argparse::ArgumentParser& parser, const Config& config)
    : _showstack(parser.get<bool>("--showstack"))
    , _showtimeline(parser.get<bool>("--showtimeline"))
    , _config(config)
{
    reloadSourceFile();
}

// Recursively convert a Python object to nlohmann::json.
// Handles all types that can appear in StackAction args.
static json pyToJson(py::handle h)
{
    auto obj = py::reinterpret_borrow<py::object>(h);
    if (obj.is_none()) return nullptr;
    if (py::isinstance<py::bool_>(obj)) return obj.cast<bool>();
    if (py::isinstance<py::int_>(obj)) return obj.cast<int64_t>();
    if (py::isinstance<py::float_>(obj)) return obj.cast<double>();
    if (py::isinstance<py::str>(obj)) return obj.cast<std::string>();
    if (py::isinstance<py::dict>(obj)) {
        json d;
        for (auto [k, v] : obj.cast<py::dict>())
            d[k.cast<std::string>()] = pyToJson(v);
        return d;
    }
    if (py::isinstance<py::list>(obj) || py::isinstance<py::tuple>(obj)) {
        json arr = json::array();
        for (auto item : obj)
            arr.push_back(pyToJson(item));
        return arr;
    }
    // Numeric types wrapping float (e.g. wufloat)
    if (py::hasattr(obj, "__float__")) {
        try {
            return obj.cast<double>();
        } catch (...) {
        }
    }
    // Custom types with explicit serialization (e.g. rgba → [r,g,b,a], v2 → {x,y}).
    // Must come before __dict__ so rgba doesn't become {"r":…} instead of [r,g,b,a].
    if (py::hasattr(obj, "jsonSerialization")) {
        return pyToJson(obj.attr("jsonSerialization")());
    }
    // Fallback: convert via __dict__ (StackAction subclasses)
    if (py::hasattr(obj, "__dict__")) {
        return pyToJson(obj.attr("__dict__"));
    }
    return obj.cast<std::string>();
}

void VC::Core::reloadSourceFile()
{
    _inputs.clear();
    _waits.clear();
    _timestamps.clear();
    _nbFrame = 0;
    _index = 0;
    _lastRenderedIndex = SIZE_MAX;
    _cachedMeshes.clear();

    try {
        auto serialize = py::module_::import("videocode.serialize");
        VC_TIME("execScene (in-process)", serialize.attr("execScene")(_config.sourceFile));

        auto     ctx = py::module_::import("videocode.context").attr("Context");
        py::list stack = ctx.attr("stack");

        VC_TIME("executeStack", executeStack(stack));

    } catch (const py::error_already_set& e) {
        std::cerr << "\nError in source file '" << _config.sourceFile << "':\n"
                  << e.what() << "\n";
    }
}

void VC::Core::executeStack(const py::list& stack)
{
    for (const auto& item : stack) {
        auto obj = py::reinterpret_borrow<py::object>(item);
        auto action = obj.attr("action").cast<std::string>();

        if (_showstack) {
            Debug.logStack(pyToJson(obj));
        }

        if (action == "Create") {
            auto type = obj.attr("type").cast<std::string>();
            json args = pyToJson(obj.attr("args"));
            _inputs.push_back(Factory::inputs.at(type)(args));

        } else if (action == "Apply") {
            ssize_t index = obj.attr("input").cast<int>();
            json    args = pyToJson(obj.attr("args"));
            size_t  start = args["start"];
            size_t  duration = args["duration"];
            size_t  lastFrame = start + duration;

            if (lastFrame > _nbFrame)
                _nbFrame = lastFrame;

            json s = pyToJson(obj);
            _inputs[index]->add(s);

        } else if (action == "Wait") {
            size_t n = obj.attr("n").cast<int>();

            for (size_t i = 0; i < n; i++)
                _waits[_nbFrame + i] = _nbFrame == 0 ? 0 : (_nbFrame - 1);
            _nbFrame += n;

        } else if (action == "Timestamp") {
            auto   name = obj.attr("name").cast<std::string>();
            size_t time = obj.attr("time").cast<int>();
            _timestamps[time] = name;

        } else {
            throw Error("Invalid action: " + action);
        }
    }
}

std::vector<Mesh> VC::Core::generateMeshes()
{
    size_t renderIndex = _index;
    auto   potentialIndex = _waits.find(_index);
    if (potentialIndex != _waits.end()) {
        renderIndex = potentialIndex->second;
    }

    if (renderIndex != _lastRenderedIndex) {
        _cachedMeshes.clear();
        VC_TIME("generateMeshes", {
            for (auto& i : _inputs) {
#ifdef VC_DEBUG_ON
                auto _tInput0 = std::chrono::high_resolution_clock::now();
#endif
                auto meta = i->getMetadata(renderIndex);
                if (!meta.hidden && meta.opacity != 0) {
                    auto mesh = i->getMesh(meta, _config);
                    if (auto* a = dynamic_cast<AInput*>(i.get()))
                        mesh.effects = a->getActiveEffectsAtFrame(renderIndex);
                    _cachedMeshes.push_back(std::move(mesh));
                }
#ifdef VC_DEBUG_ON
                auto _tInputMs = std::chrono::duration_cast<std::chrono::microseconds>(
                                     std::chrono::high_resolution_clock::now() - _tInput0
                )
                                     .count();
                if (_tInputMs > 500)
                    VC_LOG(std::format("[timer] getMesh input#{}: {}µs\n", &i - &_inputs[0], _tInputMs));
#endif
            }
        });
        _lastRenderedIndex = renderIndex;
        _meshesRebuilt = true;
    } else {
        _meshesRebuilt = false;
    }

    // load next frame if not in pause and not at the end
    if (_paused == false && _nbFrame && _index < _nbFrame - 1) {
        _index += 1;
        _indexChanged = true;
    } else {
        _indexChanged = false;
    }

    return _cachedMeshes;
}

#define currIndex(i, s) (s == 0 ? 0 : (i + 1))

void VC::Core::pause()
{
    _paused = !_paused;
    _indexChanged = true;
    std::cout << std::format("Timeline {} at frame {}/{}.", _paused ? "paused" : "unpaused", currIndex(_index, _nbFrame), _nbFrame) << std::endl;
}

void VC::Core::goToFirstFrame()
{
    if (_index != 0) {
        _index = 0;
        _indexChanged = true;
    }
    std::cout << std::format("Jumped backward to the first frame {}/{}.", currIndex(_index, _nbFrame), _nbFrame) << std::endl;
}

void VC::Core::goToLastFrame()
{
    if (_nbFrame != 0) {
        _index = _nbFrame - 1;
        _indexChanged = true;
    }
    std::cout << std::format("Jumped forward to the last frame {}/{}.", currIndex(_index, _nbFrame), _nbFrame) << std::endl;
}

void VC::Core::goToPrevTimestamp()
{
    auto it = _timestamps.lower_bound(_index);

    if (it == _timestamps.begin()) {
        return;
    }

    --it;

    auto index = it->first;
    auto name = it->second;

    if (_index < _nbFrame && _index >= 0) {
        _index = index;
        _indexChanged = true;
    }

    std::cout << std::format("Jumped backward to the timestamp {} at frame {}/{}.", name, currIndex(_index, _nbFrame), _nbFrame) << std::endl;
}

void VC::Core::goToNextTimestamp()
{
    auto it = _timestamps.lower_bound(_index);

    if (it == _timestamps.end()) {
        return;
    }

    auto index = it->first;
    auto name = it->second;

    if (_index < _nbFrame && _index >= 0) {
        _index = index;
        _indexChanged = true;
    }

    std::cout << std::format("Jumped forward to the timestamp {} at frame {}/{}.", name, currIndex(_index, _nbFrame), _nbFrame) << std::endl;
}

void VC::Core::backwardFrame(size_t n)
{
    if (_index >= n) {
        _index -= n;
        _indexChanged = true;
    } else {
        goToFirstFrame();
        return;
    }
    std::cout << std::format("Jumped backward to the frame {}/{}.", currIndex(_index, _nbFrame), _nbFrame) << std::endl;
}

void VC::Core::forwardFrame(size_t n)
{
    if (n < _nbFrame - _index) {
        _index += n;
        _indexChanged = true;
    } else {
        goToLastFrame();
        return;
    }
    std::cout << std::format("Jumped forward to the frame {}/{}.", currIndex(_index, _nbFrame), _nbFrame) << std::endl;
}

void VC::Core::uploadTextures(VC::VulkanWidget* widget)
{
    for (auto& inputPtr : _inputs) {
        if (Image* img = dynamic_cast<Image*>(inputPtr.get())) {
            VkDescriptorSet desc = widget->uploadTexture(img->getBase());
            img->setTextureDescriptor(desc);
        }
    }
}

void VC::Core::uploadTextures(std::function<VkDescriptorSet(const cv::Mat&)> uploadFn)
{
    for (auto& inputPtr : _inputs) {
        if (Image* img = dynamic_cast<Image*>(inputPtr.get())) {
            img->setTextureDescriptor(uploadFn(img->getBase()));
        }
    }
}
