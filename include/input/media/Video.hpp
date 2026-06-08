/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Video
*/

#pragma once

#include <functional>
#include <vulkan/vulkan.h>
#include <opencv2/videoio.hpp>

#include "input/AInput.hpp"

class Video final : public AInput
{
public:

    Video(json::object_t&& args);
    ~Video() = default;

    Mesh    getMesh(const Metadata& meta, const Config& config) override;
    cv::Mat getFrameAt(size_t index);

    const cv::Mat& currentFrame() const { return _currentFrame; }
    void setDescriptor(VkDescriptorSet d) { _descriptor = d; }
    void setReuploadFn(std::function<void(const cv::Mat&)> fn) { _reupload = std::move(fn); }

    size_t _nbFrame{0};
    size_t _playbackLength{0}; // _nbFrame minus all cut ranges — what Core sees as this Video's contribution to the timeline

private:

    size_t mapToSourceIndex(size_t playbackIndex) const;

    cv::VideoCapture _video;
    cv::Mat          _currentFrame;
    size_t           _lastIndex{SIZE_MAX};
    VkDescriptorSet  _descriptor{VK_NULL_HANDLE};
    std::function<void(const cv::Mat&)> _reupload;
    std::vector<std::pair<size_t, size_t>> _cuts; // sorted, merged, non-overlapping [start, end) ranges of source frames to skip
};
