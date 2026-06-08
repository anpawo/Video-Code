/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Video
*/

#include "input/media/Video.hpp"

#include <algorithm>
#include <opencv2/imgproc.hpp>

#include "utils/Exception.hpp"
#include "vulkan/MeshFactory.hpp"

Video::Video(json::object_t&& args)
    : AInput(std::move(args))
{
    std::string filepath = _baseArgs.at("filepath");

    _video.open(filepath);

    if (!_video.isOpened()) {
        throw Error("Could not load Video: " + filepath);
    }

    _nbFrame = static_cast<size_t>(_video.get(cv::CAP_PROP_FRAME_COUNT));

    if (_nbFrame == 0) {
        throw Error("Video has no frames: " + filepath);
    }

    // Parse, clamp and merge the requested cut ranges into sorted, non-overlapping
    // [start, end) pairs so mapToSourceIndex can walk them in a single forward pass.
    if (_baseArgs.contains("cuts")) {
        for (const auto& raw : _baseArgs.at("cuts")) {
            auto   pair  = raw.get<std::vector<size_t>>();
            size_t start = std::min(pair[0], _nbFrame);
            size_t end   = std::min(pair[1], _nbFrame);

            if (end > start) {
                _cuts.push_back({start, end});
            }
        }
    }

    std::sort(_cuts.begin(), _cuts.end());

    std::vector<std::pair<size_t, size_t>> merged;
    for (const auto& cut : _cuts) {
        if (!merged.empty() && cut.first <= merged.back().second) {
            merged.back().second = std::max(merged.back().second, cut.second);
        } else {
            merged.push_back(cut);
        }
    }
    _cuts = std::move(merged);

    size_t totalCut = 0;
    for (const auto& [start, end] : _cuts) {
        totalCut += end - start;
    }
    _playbackLength = (totalCut < _nbFrame) ? (_nbFrame - totalCut) : 1;

    _lastIndex    = mapToSourceIndex(0);
    _currentFrame = getFrameAt(_lastIndex);
}

// Maps a position in the cut-down playback timeline back to the corresponding
// source-video frame index, by shifting forward over every cut range that the
// (progressively shifted) index has reached. Cuts are sorted and non-overlapping,
// so a single forward pass suffices.
size_t Video::mapToSourceIndex(size_t playbackIndex) const
{
    size_t source = playbackIndex;

    for (const auto& [start, end] : _cuts) {
        if (source >= start) {
            source += end - start;
        } else {
            break;
        }
    }

    return source;
}

cv::Mat Video::getFrameAt(size_t index)
{
    if (index >= _nbFrame) {
        index = _nbFrame - 1;
    }

    cv::Mat frame;

    while (true) {
        _video.set(cv::CAP_PROP_POS_FRAMES, static_cast<double>(index));
        _video.read(frame);

        if (frame.empty()) {
            if (index == 0) {
                throw Error("Video has no readable frames: " + _baseArgs.at("filepath").get<std::string>());
            }
            index--;
        } else {
            break;
        }
    }

    if (frame.channels() != 4) {
        cv::cvtColor(frame, frame, cv::COLOR_BGR2BGRA);
    }

    return frame;
}

Mesh Video::getMesh(const Metadata& meta, const Config& config)
{
    size_t playbackIndex = meta.args.at("index");

    if (playbackIndex >= _playbackLength) {
        playbackIndex = _playbackLength - 1;
    }

    size_t index = mapToSourceIndex(playbackIndex);

    if (index != _lastIndex) {
        _currentFrame = getFrameAt(index);
        _lastIndex    = index;
        if (_reupload) {
            _reupload(_currentFrame);
        }
    }

    float w = static_cast<float>(_currentFrame.cols);
    float h = static_cast<float>(_currentFrame.rows);

    if (meta.args.contains("width"))  w = meta.args.at("width").get<float>();
    if (meta.args.contains("height")) h = meta.args.at("height").get<float>();

    MeshFactory factory({w, h}, meta, config);

    float    opacity = meta.opacity / 255.f;
    uint16_t base    = factory.vertexCount();
    factory.addVertex(0.f, 0.f, 0.f, 0.f, opacity);
    factory.addVertex(w,   0.f, 1.f, 0.f, opacity);
    factory.addVertex(w,   h,   1.f, 1.f, opacity);
    factory.addVertex(0.f, h,   0.f, 1.f, opacity);

    factory.addIndex(base + 0);
    factory.addIndex(base + 1);
    factory.addIndex(base + 2);
    factory.addIndex(base + 0);
    factory.addIndex(base + 2);
    factory.addIndex(base + 3);

    Mesh mesh         = factory.generateMesh();
    mesh.hasTexture   = true;
    mesh.textureDescriptor = _descriptor;
    return mesh;
}
