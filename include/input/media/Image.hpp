/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Image
*/

#pragma once

#include <vulkan/vulkan.h>
#include <opencv2/core/mat.hpp>

#include "input/shape/BezierPath.hpp"

class Image final : public BezierPath
{
public:

    Image(json::object_t&& args);
    ~Image() override = default;

    Mesh    getMesh(const Metadata& meta, const Config& config) override;
    cv::Mat getBaseMatrix(const json::object_t& args);

    const cv::Mat& getBase() const { return _base; }
    void setTextureDescriptor(VkDescriptorSet d) { _descriptor = d; }

protected:

    bool isTextured() const override { return true; }
    VkDescriptorSet textureDescriptor() const override { return _descriptor; }

private:

    cv::Mat         _base;
    VkDescriptorSet _descriptor = VK_NULL_HANDLE;
};
