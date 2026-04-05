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

#include "core/Config.hpp"
#include "input/Metadata.hpp"
#include "shader/IVertexShader.hpp"
#include "vulkan/Mesh.hpp"

struct MeshFactory
{
    Mesh mesh;

    cv::Matx33f M;
    cv::Size2f  localSize;

    float windowWidth;
    float windowHeight;

    // ---

    MeshFactory(const cv::Size2f &localSize, const Metadata &meta, const Config &config)
        : M(getTransformationMatrixFromMetadata(localSize, meta))
        , localSize(localSize)
        , windowWidth(config.windowWidth)
        , windowHeight(config.windowHeight)
    {
    }

    // Shape calls this for each local-space corner
    void addVertex(float localX, float localY, const cv::Vec4b &color)
    {
        cv::Matx31f world = M * cv::Matx31f{localX, localY, 1.f};

        float ndcX = world(0) / windowWidth - 1.f;
        float ndcY = world(1) / windowHeight - 1.f;

        float u = (localSize.width  > 0.f) ? localX / localSize.width  : 0.f;
        float v = (localSize.height > 0.f) ? localY / localSize.height : 0.f;

        mesh.vertices.push_back(Vertex{
            {ndcX, ndcY},
            {u, v},
            {color[0] / 255.f,
             color[1] / 255.f,
             color[2] / 255.f,
             color[3] / 255.f
            }
        });
    }

    void addVertex(float localX, float localY, float u, float v) // textured variant
    {
        cv::Matx31f world = M * cv::Matx31f{localX, localY, 1.f};

        float ndcX = world(0) / windowWidth * 2.f - 1.f;
        float ndcY = world(1) / windowHeight * 2.f - 1.f;

        mesh.vertices.push_back(Vertex{
            {ndcX, ndcY},
            {u, v},
            {}
        });
    }

    uint16_t vertexCount() const
    {
        return static_cast<uint16_t>(mesh.vertices.size());
    }

    MeshFactory &addIndex(uint16_t idx)
    {
        mesh.indices.push_back(idx);
        return *this;
    }

    MeshFactory &setIndices(std::vector<uint16_t> indices)
    {
        mesh.indices = std::move(indices);
        return *this;
    }

    // MeshBuilder &setTexture(TextureDescriptor *descriptor)
    // {
    //     mesh.hasTexture = true;
    //     mesh.textureDescriptor = descriptor;
    //     return *this;
    // }

    template <typename T>
    MeshFactory &setPushConstants(const T &pc)
    {
        const uint8_t *bytes = reinterpret_cast<const uint8_t *>(&pc);
        mesh.pushConstantData.assign(bytes, bytes + sizeof(T));
        return *this;
    }

    Mesh generateMesh()
    {
        return std::move(mesh);
    }
};
