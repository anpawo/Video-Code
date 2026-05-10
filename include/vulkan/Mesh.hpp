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
#include <string>
#include <vector>

#include "Vertex.hpp"

// A fragment shader effect active on a mesh at a given frame.
// name   = shader class name ("Blur", "Grayscale", …)
// params = ordered float values from the shader's args (shaderParams())
struct ActiveEffect
{
    std::string         name;
    std::vector<float>  params;
};

struct Mesh
{
    std::vector<Vertex>      vertices;
    std::vector<uint16_t>    indices;
    bool                     hasTexture        = false;
    VkDescriptorSet          textureDescriptor = nullptr;
    std::vector<ActiveEffect> effects;
};
