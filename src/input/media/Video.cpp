/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Video
*/

#include "input/media/Video.hpp"

#include <algorithm>
#include <cmath>
#include <opencv2/imgproc.hpp>

#include "utils/Exception.hpp"
#include "vulkan/MeshFactory.hpp"

Video::Video(json::object_t&& args)
    : BezierPath(std::move(args))
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
            auto   pair = raw.get<std::vector<size_t>>();
            size_t start = std::min(pair[0], _nbFrame);
            size_t end = std::min(pair[1], _nbFrame);

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

    // Speed ramps are expressed in playback space (the same post-cut index space
    // `_playbackLength` describes), so they can only be parsed/clamped once
    // `_playbackLength` is known. `end` is clamped to `_playbackLength` the same
    // way cuts clamp to `_nbFrame` above.
    if (_baseArgs.contains("speedRamps")) {
        for (const auto& raw : _baseArgs.at("speedRamps")) {
            auto   triple = raw.get<std::vector<double>>();
            size_t start = std::min(static_cast<size_t>(triple[0]), _playbackLength);
            size_t end = std::min(static_cast<size_t>(triple[1]), _playbackLength);
            double rate = triple[2];

            if (end > start) {
                _speedRamps.push_back({start, end, rate});
            }
        }
    }

    // The Python side already rejects overlapping segments; sorting here just
    // lets mapToSourceIndex do a simple ordered scan.
    std::sort(_speedRamps.begin(), _speedRamps.end(),
              [](const SpeedRamp& a, const SpeedRamp& b) { return a.playbackStart < b.playbackStart; });

    _lastIndex = mapToSourceIndex(0);
    _currentFrame = getFrameAt(_lastIndex);
}

// The original cuts-only mapping: shifts forward over every cut range that the
// (progressively shifted) index has reached. Cuts are sorted and non-overlapping,
// so a single forward pass suffices. Kept standalone (rather than folded into
// mapToSourceIndex) so: (a) cuts-only behavior — no speedRamps at all — stays
// byte-for-byte identical to before speed ramps existed, and (b) a speed-ramp
// segment can anchor its own rate math on "what the plain cuts-only mapping
// would have produced at the start of this ramp".
size_t Video::mapCutsOnly(size_t playbackIndex) const
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

// Maps a position in the cut-down playback timeline back to the corresponding
// source-video frame index. Piecewise: `_cuts` and `_speedRamps` both carve up
// playback space, but only `_speedRamps` need special per-segment rate math —
// everywhere else (including a `rate == 1.0` ramp, which is a documented no-op)
// the plain cuts-only additive mapping applies unchanged.
//
// A ramp segment anchors on `mapCutsOnly(playbackStart)` — the source frame the
// plain mapping would show at the start of the ramp window — then advances by
// `round((playbackIndex - playbackStart) * rate)` source frames from there:
// rate 1 preserves the anchor+delta identity, 0 freezes on the anchor frame,
// negative rates walk the source index backwards (reverse playback), and the
// result is clamped into the video's valid source-frame range at the edges.
//
// Known limitation: a cut boundary falling *inside* a non-1x ramp window isn't
// accounted for by the ramp's own math (only by the anchor, which is computed
// once at the ramp's start) — segments aren't expected to straddle a cut in
// practice, and this mirrors the "no frame-blending" simplicity of the rest of
// this feature.
size_t Video::mapToSourceIndex(size_t playbackIndex) const
{
    for (const auto& ramp : _speedRamps) {
        if (playbackIndex < ramp.playbackStart) {
            break; // sorted ascending — no later ramp can contain this index either
        }
        if (playbackIndex >= ramp.playbackEnd) {
            continue;
        }
        if (ramp.rate == 1.0) {
            break; // no-op ramp: fall through to the plain additive mapping below
        }

        size_t    anchor = mapCutsOnly(ramp.playbackStart);
        long long delta = static_cast<long long>(playbackIndex - ramp.playbackStart);
        long long offset = (ramp.rate == 0.0) ? 0 : static_cast<long long>(std::llround(static_cast<double>(delta) * ramp.rate));
        long long source = static_cast<long long>(anchor) + offset;

        if (source < 0) {
            source = 0;
        } else if (source >= static_cast<long long>(_nbFrame)) {
            source = static_cast<long long>(_nbFrame) - 1;
        }

        return static_cast<size_t>(source);
    }

    return mapCutsOnly(playbackIndex);
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
    size_t playbackIndex = meta.frameIndex;

    if (playbackIndex >= _playbackLength) {
        playbackIndex = _playbackLength - 1;
    }

    size_t index = mapToSourceIndex(playbackIndex);

    if (index != _lastIndex) {
        _currentFrame = getFrameAt(index);
        _lastIndex = index;
        if (_reupload) {
            _reupload(_currentFrame);
        }
    }

    bool hasCustomShape = meta.pointsPtr && meta.pointsPtr->size() >= 4 && meta.pointsPtr->size() % 2 == 0;
    if (hasCustomShape)
        return BezierPath::getMesh(meta, config);

    float w = static_cast<float>(_currentFrame.cols);
    float h = static_cast<float>(_currentFrame.rows);

    if (meta.args().contains("width")) w = meta.args().at("width").get<float>();
    if (meta.args().contains("height")) h = meta.args().at("height").get<float>();

    MeshFactory factory({w, h}, meta, config);

    float    opacity = meta.opacity / 255.f;
    uint32_t base = factory.vertexCount();
    factory.addVertex(0.f, 0.f, 0.f, 0.f, opacity);
    factory.addVertex(w, 0.f, 1.f, 0.f, opacity);
    factory.addVertex(w, h, 1.f, 1.f, opacity);
    factory.addVertex(0.f, h, 0.f, 1.f, opacity);

    factory.addIndex(base + 0);
    factory.addIndex(base + 1);
    factory.addIndex(base + 2);
    factory.addIndex(base + 0);
    factory.addIndex(base + 2);
    factory.addIndex(base + 3);

    Mesh mesh = factory.generateMesh();
    mesh.hasTexture = true;
    mesh.textureDescriptor = _descriptor;
    return mesh;
}
