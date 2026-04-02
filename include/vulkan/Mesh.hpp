/*
** EPITECH PROJECT, 2026
** video-code
** File description:
** Vertex
*/

#pragma once
#include <vulkan/vulkan.h>

#include <any>
#include <cstdint>
#include <vector>

#include "Vertex.hpp"

struct Mesh
{
    std::vector<Vertex>   vertices;
    std::vector<uint16_t> indices;
    bool                  hasTexture = false;
    VkDescriptorSet       textureDescriptor = nullptr;
    std::any              pushConstants; // RectPushConstants, CirclePushConstants, etc.
};
