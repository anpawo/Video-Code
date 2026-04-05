/*
** EPITECH PROJECT, 2026
** video-code
** File description:
** Vertex
*/

#pragma once
#include <vulkan/vulkan.h>

#include <cstdint>
#include <opencv2/core/matx.hpp>
#include <opencv2/core/types.hpp>
#include <vector>

#include "Vertex.hpp"

struct Mesh
{
    std::vector<Vertex>   vertices;
    std::vector<uint16_t> indices;
    bool                  hasTexture = false;
    VkDescriptorSet       textureDescriptor = nullptr;
    std::vector<uint8_t>  pushConstantData; // raw bytes for vkCmdPushConstants
};
