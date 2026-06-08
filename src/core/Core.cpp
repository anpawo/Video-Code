/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Core
*/

#include "core/Core.hpp"

#include <pybind11/embed.h>
#include <pybind11/stl.h>

#include <chrono>
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
#include "input/media/Video.hpp"
// #include "input/media/Video.hpp"
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
        // Keys may be ints (Context.stack is keyed by inputIdx / frameIdx, with -1 the
        // Create sentinel) — stringify via py::str() rather than a direct cast.
        for (auto [k, v] : obj.cast<py::dict>())
            d[py::str(k).cast<std::string>()] = pyToJson(v);
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
    size_t savedIndex = _index;

    // Startup timing — printed when compiled with -DVC_VERBOSE.
#ifdef VC_VERBOSE
    using Clock = std::chrono::high_resolution_clock;
    using Ms = std::chrono::duration<double, std::milli>;
    auto _t_reload = Clock::now();
    auto _t = Clock::now();
    auto _step = [&](const char* name) {
        double ms = std::chrono::duration_cast<Ms>(Clock::now() - _t).count();
        std::cout << std::format("[startup] {:35s} {:7.1f}ms\n", name, ms);
        _t = Clock::now();
    };
#else
    auto _step = [](const char*) {};
#endif

    try {
        auto serialize = py::module_::import("videocode.serialize");
        VC_TIME("execScene (in-process)", serialize.attr("execScene")(_config.sourceFile));
        _step("execScene (Python in-process)");

        auto     ctx = py::module_::import("videocode.context").attr("Context");
        py::dict stack = ctx.attr("stack");
        py::list events = ctx.attr("events");

        VC_TIME("executeStack", executeStack(stack, events));
        _step("executeStack (C++ reads py::dict)");

        // Extend _nbFrame to cover any Video inputs whose duration exceeds the stack's range.
        for (const auto& inputPtr : _inputs) {
            if (const Video* vid = dynamic_cast<const Video*>(inputPtr.get())) {
                if (vid->_playbackLength > _nbFrame)
                    _nbFrame = vid->_playbackLength;
            }
        }

        // Force a redraw with the (possibly partially-rebuilt) input set. Only invalidated
        // on success — a broken edit leaves the last-good render on screen instead of
        // blanking it.
        _lastRenderedIndex = SIZE_MAX;
        _cachedMeshes.clear();

    } catch (const py::error_already_set& e) {
        std::cerr << "\nError in source file '" << _config.sourceFile << "':\n"
                  << e.what() << "\n";
    }

    _index = (_nbFrame > 0) ? std::min(savedIndex, _nbFrame - 1) : 0;

#ifdef VC_VERBOSE
    double total_ms = std::chrono::duration_cast<Ms>(Clock::now() - _t_reload).count();
    std::cout << std::format("[startup] === reloadSourceFile() total: {:.1f}ms ===\n", total_ms);
#endif
}

void VC::Core::rebuildInput(size_t idx, const py::dict& inputData, bool reuseExisting)
{
    AInput*                 target = nullptr;
    std::unique_ptr<IInput> freshInput;

    if (reuseExisting && idx < _inputs.size())
        target = dynamic_cast<AInput*>(_inputs[idx].get());

    if (target) {
        // Create entry unchanged — keep the object alive (and its loaded media / GPU
        // descriptor / geometry caches) and just rewind its modification history.
        target->resetModifications();
    } else {
        py::dict create = inputData[py::int_(-1)].cast<py::dict>();
        auto     type   = create["type"].cast<std::string>();
        json     args   = pyToJson(create["args"]);

        if (_showstack)
            Debug.logStack({{"action", "Create"}, {"type", type}, {"args", args}});

        freshInput = Factory::inputs.at(type)(args);
        target     = dynamic_cast<AInput*>(freshInput.get());
    }

    // Replay Apply entries in the dict's natural (insertion / chronological) order —
    // AInput::add() is cumulative/order-dependent (Metadata mutation, effect timeline).
    for (auto [rawFrame, rawShaders] : inputData) {
        ssize_t frameIdx = rawFrame.cast<ssize_t>();
        if (frameIdx < 0) continue; // skip Create sentinel at -1

        for (auto [rawKey, rawEntry] : rawShaders.cast<py::dict>()) {
            std::string dictKey = rawKey.cast<std::string>();
            // "Args:argName" → shaderName = "Args"; everything else is verbatim.
            std::string shaderName = dictKey.substr(0, dictKey.find(':'));

            json        entry = pyToJson(py::reinterpret_borrow<py::object>(rawEntry));
            std::string shaderType = entry["type"].get<std::string>();
            json        args2 = entry["args"];

            json modification = {
                {"name", shaderName},
                {"type", shaderType},
                {"args", args2},
            };

            if (_showstack)
                Debug.logStack({{"action", "Apply"}, {"input", (ssize_t)idx}, {"name", shaderName}, {"type", shaderType}, {"args", args2}});

            target->add(modification);
        }
    }

    // Only freshly-constructed Image/Video need a texture (re)upload — a reused input's
    // descriptor still points at the same (unchanged) media and remains valid.
    if (freshInput) {
        if (idx >= _inputs.size())
            _inputs.resize(idx + 1);

        if (dynamic_cast<Image*>(freshInput.get()) || dynamic_cast<Video*>(freshInput.get()))
            _pendingTextureUpload.push_back(idx);

        _inputs[idx] = std::move(freshInput);
    }
}

void VC::Core::executeStack(const py::dict& stack, const py::list& events)
{
    // Snapshot every input's full subtree (Create + all frame/shader entries) as JSON —
    // a stable, order-independent value we can diff against the previous reload.
    std::map<int, json> newSnapshot;
    for (auto [rawIdx, rawInputData] : stack) {
        int idx = rawIdx.cast<int>();
        newSnapshot[idx] = pyToJson(py::reinterpret_borrow<py::object>(rawInputData));
    }

    // Only diff input-by-input when the set of input indices is unchanged — adding/
    // removing an input reshuffles Python's sequential index counter, so positional
    // diffing would silently compare unrelated inputs. Fall back to a full rebuild then.
    bool sameIndexSet = (_stackSnapshot.size() == newSnapshot.size());
    if (sameIndexSet) {
        for (const auto& [idx, _] : newSnapshot) {
            if (!_stackSnapshot.count(idx)) {
                sameIndexSet = false;
                break;
            }
        }
    }

    _pendingTextureUpload.clear();
    if (!sameIndexSet) {
        _inputs.clear();
        _inputs.resize(newSnapshot.size());
    }

    for (auto [rawIdx, rawInputData] : stack) {
        int      idx       = rawIdx.cast<int>();
        py::dict inputData = rawInputData.cast<py::dict>();

        bool known = sameIndexSet && _stackSnapshot.count(idx);

        if (known && _stackSnapshot[idx] == newSnapshot[idx])
            continue; // nothing changed at all — keep the existing AInput (and its caches/textures) untouched

        // Reuse the existing object (skip its constructor — e.g. Image/Video file I/O)
        // when only its modifications changed, i.e. its Create entry ("-1") is identical.
        bool reuseExisting = known
            && _stackSnapshot[idx].contains("-1")
            && newSnapshot[idx].contains("-1")
            && _stackSnapshot[idx]["-1"] == newSnapshot[idx]["-1"];

        rebuildInput((size_t)idx, inputData, reuseExisting);
    }

    _stackSnapshot = std::move(newSnapshot);

    // Recompute _nbFrame from the (now up-to-date) snapshot — cheap pure-JSON scan.
    _nbFrame = 0;
    for (const auto& [idx, subtree] : _stackSnapshot) {
        for (const auto& [frameKey, shaders] : subtree.items()) {
            if (frameKey == "-1") continue;
            for (const auto& [shaderKey, entry] : shaders.items()) {
                size_t start = entry["args"]["start"];
                size_t duration = entry["args"]["duration"];
                size_t lastFrame = start + duration;
                if (lastFrame > _nbFrame)
                    _nbFrame = lastFrame;
            }
        }
    }

    // Pass 3: Wait and Timestamp events (absolute positions stored by Python).
    _waits.clear();
    _timestamps.clear();
    for (const auto& item : events) {
        auto obj = py::reinterpret_borrow<py::object>(item);
        auto action = obj.attr("action").cast<std::string>();

        if (action == "Wait") {
            size_t start = obj.attr("start").cast<size_t>();
            size_t n = obj.attr("n").cast<size_t>();
            for (size_t i = 0; i < n; i++)
                _waits[start + i] = start == 0 ? 0 : (start - 1);
            size_t waitEnd = start + n;
            if (waitEnd > _nbFrame)
                _nbFrame = waitEnd;

        } else if (action == "Timestamp") {
            auto   name = obj.attr("name").cast<std::string>();
            size_t time = obj.attr("time").cast<size_t>();
            _timestamps[time] = name;
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
    // Only (re)upload textures for inputs rebuilt by the last executeStack() — reusing
    // an unchanged Image/Video's existing descriptor set avoids leaking GPU textures.
    for (size_t idx : _pendingTextureUpload) {
        IInput* inputPtr = _inputs[idx].get();
        if (Image* img = dynamic_cast<Image*>(inputPtr)) {
            VkDescriptorSet desc = widget->uploadTexture(img->getBase());
            img->setTextureDescriptor(desc);
        } else if (Video* vid = dynamic_cast<Video*>(inputPtr)) {
            VkDescriptorSet desc = widget->uploadTexture(vid->currentFrame());
            vid->setDescriptor(desc);
            vid->setReuploadFn([widget, desc](const cv::Mat& mat) {
                widget->updateTexturePixels(desc, mat);
            });
        }
    }
    _pendingTextureUpload.clear();
}

void VC::Core::uploadTextures(
    std::function<VkDescriptorSet(const cv::Mat&)>       uploadFn,
    std::function<void(VkDescriptorSet, const cv::Mat&)> reuploadFn
)
{
    for (size_t idx : _pendingTextureUpload) {
        IInput* inputPtr = _inputs[idx].get();
        if (Image* img = dynamic_cast<Image*>(inputPtr)) {
            img->setTextureDescriptor(uploadFn(img->getBase()));
        } else if (Video* vid = dynamic_cast<Video*>(inputPtr)) {
            VkDescriptorSet desc = uploadFn(vid->currentFrame());
            vid->setDescriptor(desc);
            if (reuploadFn) {
                vid->setReuploadFn([desc, reuploadFn](const cv::Mat& mat) {
                    reuploadFn(desc, mat);
                });
            }
        }
    }
    _pendingTextureUpload.clear();
}
