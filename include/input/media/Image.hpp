/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Image
*/

#pragma once

#include <vulkan/vulkan.h>
#include <opencv2/core/mat.hpp>

#include "input/AInput.hpp"

class Image final : public AInput
{
public:

    Image(json::object_t&& args);
    ~Image() = default;

    Mesh    getMesh(const Metadata& meta, const Config& config) override;
    cv::Mat getBaseMatrix(const json::object_t& args);

    const cv::Mat& getBase() const { return _base; }
    void setTextureDescriptor(VkDescriptorSet d) { _descriptor = d; }

private:

    cv::Mat         _base;
    VkDescriptorSet _descriptor = VK_NULL_HANDLE;
};
