/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Video
*/

#pragma once

#include <vulkan/vulkan.h>

#include <functional>
#include <opencv2/videoio.hpp>

#include "input/shape/BezierPath.hpp"

class Video final : public BezierPath
{
public:

    Video(json::object_t&& args);
    ~Video() override = default;

    Mesh    getMesh(const Metadata& meta, const Config& config) override;
    cv::Mat getFrameAt(size_t index);

    const cv::Mat& currentFrame() const { return _currentFrame; }

    void setDescriptor(VkDescriptorSet d) { _descriptor = d; }

    void setReuploadFn(std::function<void(const cv::Mat&)> fn) { _reupload = std::move(fn); }

    size_t _nbFrame{0};
    size_t _playbackLength{0}; // _nbFrame minus all cut ranges — what Core sees as this Video's contribution to the timeline

protected:

    bool isTextured() const override { return true; }

    VkDescriptorSet textureDescriptor() const override { return _descriptor; }

private:

    // A speed-ramp segment: over playback-space range [playbackStart, playbackEnd),
    // the source index advances at `rate` source-frames per playback-frame instead
    // of the implicit 1x (0 = freeze-frame, negative = reverse). Anchored on the
    // plain cuts-only mapping of `playbackStart` — see mapToSourceIndex.
    struct SpeedRamp {
        size_t playbackStart;
        size_t playbackEnd;
        double rate;
    };

    size_t mapToSourceIndex(size_t playbackIndex) const;
    size_t mapCutsOnly(size_t playbackIndex) const;

    cv::VideoCapture                       _video;
    cv::Mat                                _currentFrame;
    size_t                                 _lastIndex{SIZE_MAX};
    VkDescriptorSet                        _descriptor{VK_NULL_HANDLE};
    std::function<void(const cv::Mat&)>    _reupload;
    std::vector<std::pair<size_t, size_t>> _cuts; // sorted, merged, non-overlapping [start, end) ranges of source frames to skip
    std::vector<SpeedRamp>                 _speedRamps; // sorted, non-overlapping playback-space ranges with a non-default rate
};
