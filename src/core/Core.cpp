/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Core
*/

#include "core/Core.hpp"

#include <cstddef>
#include <iostream>
#include <memory>
#include <string>

#include "core/Config.hpp"
#include "input/AInput.hpp"
#include "input/IInput.hpp"
#include "input/InputFactory.hpp"
#include "input/media/Image.hpp"
#include "input/media/WebImage.hpp"
// #include "input/media/Video.hpp"
#include "utils/Exception.hpp"
#include "window/VulkanWidget.hpp"

VC::Core::Core(const argparse::ArgumentParser& parser, const Config& config)
    : _showstack(parser.get<bool>("--showstack"))
    , _showtimeline(parser.get<bool>("--showtimeline"))
    , _config(config)
{
    reloadSourceFile();
}

void VC::Core::reloadSourceFile()
{
    std::string serializedScene;

    try {
        serializedScene = serializeScene();
    } catch (const Error& e) {
        std::cerr << "\nVideoCode: Invalid source file '" << _config.sourceFile << "', could not parse the instructions." << std::endl;
        return;
    }

    _inputs.clear();
    _stack.clear();

    try {
        _stack = json::parse(serializedScene);
    } catch (const std::exception& e) {
        std::cerr << "\nVideoCode: Couldn't parse source file: " << e.what() << std::endl;
        return;
    }

    executeStack();
}

std::string VC::Core::serializeScene()
{
    std::string command = "python3 -c \"import sys; sys.path.append('./videocode');from serialize import serializeScene; print(serializeScene('video.py'))\"";

    FILE* pipe = popen(command.c_str(), "r");
    if (!pipe) {
        throw Error("Failed to load '" + _config.sourceFile + "'.");
    }

    char        buffer[4096];
    std::string result;
    while (fgets(buffer, sizeof(buffer), pipe) != nullptr) {
        result += buffer;
    }

    return result;
}

void VC::Core::executeStack()
{
    for (auto& s : _stack) {
        if (_showstack) {
            std::cout << s << std::endl;
        }

        if (s["action"] == "Create") {
            _inputs.push_back(Factory::inputs.at(s["type"])(s["args"]));

            if (s["hide"]) {
                _inputs.back()->delayAppearance();
            }

            // if (s["type"] == "Video") {
            //     auto* video = dynamic_cast<Video*>(_inputs.back().get());

            // if (video->_nbFrame > _nbFrame) {
            //     _nbFrame = video->_nbFrame;
            // }
            // }

        } else if (s["action"] == "Apply") {
            ssize_t index = s["input"];

            size_t start = s["args"]["start"];
            size_t duration = s["args"]["duration"];
            size_t lastFrame = start + duration;

            if (lastFrame > _nbFrame) {
                _nbFrame = lastFrame;
            }
            _inputs[index]->add(s);

        } else if (s["action"] == "Wait") {
            size_t n = s["n"];

            for (size_t i = 0; i < n; i++) {
                _waits[_nbFrame + i] = _nbFrame == 0 ? 0 : (_nbFrame - 1);
            }
            _nbFrame += n;

        } else {
            throw Error("Invalid action: " + s["action"].get<std::string>());
        }
    }
}

std::vector<Mesh> VC::Core::generateMeshes()
{
    size_t renderIndex = _index;
    auto potentialIndex = _waits.find(_index);
    if (potentialIndex != _waits.end()) {
        renderIndex = potentialIndex->second;
    }

    if (renderIndex != _lastRenderedIndex) {
        _cachedMeshes.clear();
        for (auto& i : _inputs) {
            auto meta = i->getMetadata(renderIndex);
            if (!meta.hidden) {
                _cachedMeshes.push_back(i->getMesh(meta, _config));
            }
        }
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

void VC::Core::backward1frame()
{
    if (_index > 0) {
        _index -= 1;
        _indexChanged = true;
    }
    std::cout << std::format("Jumped backward to the frame {}/{}.", currIndex(_index, _nbFrame), _nbFrame) << std::endl;
}

void VC::Core::forward1frame()
{
    if (_index + 1 < _nbFrame) {
        _index += 1;
        _indexChanged = true;
    }
    std::cout << std::format("Jumped forward to the frame {}/{}.", currIndex(_index, _nbFrame), _nbFrame) << std::endl;
}

void VC::Core::uploadTextures(VC::VulkanWidget* widget)
{
    for (auto& inputPtr : _inputs) {
        if (Image* img = dynamic_cast<Image*>(inputPtr.get())) {
            VkDescriptorSet desc = widget->uploadTexture(img->getBase());
            img->setTextureDescriptor(desc);
        } else if (WebImage* img = dynamic_cast<WebImage*>(inputPtr.get())) {
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
        } else if (WebImage* img = dynamic_cast<WebImage*>(inputPtr.get())) {
            img->setTextureDescriptor(uploadFn(img->getBase()));
        }
    }
}
