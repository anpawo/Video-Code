/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Image
*/

#pragma once

#include <vulkan/vulkan.h>

#include <opencv2/core/mat.hpp>
#include <string>
#include <unordered_map>

#include "input/AInput.hpp"

class WebImage final : public AInput
{
public:

    WebImage(json::object_t&& args);
    ~WebImage() = default;

    Mesh    getMesh(const Metadata& meta, const Config& config) override;
    cv::Mat getBaseMatrix(const json::object_t& args);

    const cv::Mat& getBase() const { return _base; }

    void setTextureDescriptor(VkDescriptorSet d) { _descriptor = d; }

private:

    inline static std::unordered_map<std::string, cv::Mat> _cache;

    cv::Mat         _base;
    VkDescriptorSet _descriptor = VK_NULL_HANDLE;
};
