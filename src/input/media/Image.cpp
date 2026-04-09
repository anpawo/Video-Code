/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Image
*/

#include "input/media/Image.hpp"

#include <opencv2/imgcodecs.hpp>
#include <opencv2/imgproc.hpp>

#include "utils/Exception.hpp"
#include "vulkan/MeshFactory.hpp"

Image::Image(json::object_t&& args)
    : AInput(std::move(args))
{
    _base = getBaseMatrix(_baseArgs);
}

cv::Mat Image::getBaseMatrix(const json::object_t& args)
{
    std::string filepath = args.at("filepath");

    cv::Mat mat = cv::imread(filepath, cv::IMREAD_UNCHANGED);

    if (mat.empty()) {
        throw Error("Could not load Image: " + filepath);
    }

    if (mat.channels() != 4) {
        cv::cvtColor(mat, mat, cv::COLOR_BGR2BGRA);
    }

    return mat;
}

Mesh Image::getMesh(const Metadata& meta, const Config& config)
{
    // Natural size is the image's pixel dimensions.
    // Python can override via width/height args (already in world units).
    float w = static_cast<float>(_base.cols);
    float h = static_cast<float>(_base.rows);

    if (meta.args.contains("width")) {
        w = meta.args.at("width").get<float>();
    }
    if (meta.args.contains("height")) {
        h = meta.args.at("height").get<float>();
    }

    MeshFactory factory({w, h}, meta, config);

    float opacity = meta.opacity / 255.f;
    uint16_t base = factory.vertexCount();
    factory.addVertex(0.f, 0.f, 0.f, 0.f, opacity); // top-left,     UV (0,0)
    factory.addVertex(w, 0.f, 1.f, 0.f, opacity);   // top-right,    UV (1,0)
    factory.addVertex(w, h, 1.f, 1.f, opacity);     // bottom-right, UV (1,1)
    factory.addVertex(0.f, h, 0.f, 1.f, opacity);   // bottom-left,  UV (0,1)

    factory.addIndex(base + 0);
    factory.addIndex(base + 1);
    factory.addIndex(base + 2);
    factory.addIndex(base + 0);
    factory.addIndex(base + 2);
    factory.addIndex(base + 3);

    Mesh mesh = factory.generateMesh();
    mesh.hasTexture = true;
    mesh.textureDescriptor = _descriptor; // VK_NULL_HANDLE until uploadTextures() is called
    return mesh;
}
