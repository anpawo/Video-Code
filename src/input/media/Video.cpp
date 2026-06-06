/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Video
*/

#include "input/media/Video.hpp"

#include <opencv2/imgproc.hpp>

#include "utils/Exception.hpp"
#include "vulkan/MeshFactory.hpp"

Video::Video(json::object_t&& args)
    : AInput(std::move(args))
{
    std::string filepath = _baseArgs.at("filepath");

    _video.open(filepath);

    if (!_video.isOpened()) {
        throw Error("Could not load Video: " + filepath);
    }

    _nbFrame = static_cast<size_t>(_video.get(cv::CAP_PROP_FRAME_COUNT));

    if (_nbFrame == 0) {
        throw Error("Video has no frames: " + filepath);
    }

    _currentFrame = getFrameAt(0);
    _lastIndex    = 0;
}

cv::Mat Video::getFrameAt(size_t index)
{
    if (index >= _nbFrame) {
        index = _nbFrame - 1;
    }

    cv::Mat frame;

    while (true) {
        _video.set(cv::CAP_PROP_POS_FRAMES, static_cast<double>(index));
        _video.read(frame);

        if (frame.empty()) {
            if (index == 0) {
                throw Error("Video has no readable frames: " + _baseArgs.at("filepath").get<std::string>());
            }
            index--;
        } else {
            break;
        }
    }

    if (frame.channels() != 4) {
        cv::cvtColor(frame, frame, cv::COLOR_BGR2BGRA);
    }

    return frame;
}

Mesh Video::getMesh(const Metadata& meta, const Config& config)
{
    size_t index = meta.args.at("index");

    if (index != _lastIndex) {
        _currentFrame = getFrameAt(index);
        _lastIndex    = index;
        if (_reupload) {
            _reupload(_currentFrame);
        }
    }

    float w = static_cast<float>(_currentFrame.cols);
    float h = static_cast<float>(_currentFrame.rows);

    if (meta.args.contains("width"))  w = meta.args.at("width").get<float>();
    if (meta.args.contains("height")) h = meta.args.at("height").get<float>();

    MeshFactory factory({w, h}, meta, config);

    float    opacity = meta.opacity / 255.f;
    uint16_t base    = factory.vertexCount();
    factory.addVertex(0.f, 0.f, 0.f, 0.f, opacity);
    factory.addVertex(w,   0.f, 1.f, 0.f, opacity);
    factory.addVertex(w,   h,   1.f, 1.f, opacity);
    factory.addVertex(0.f, h,   0.f, 1.f, opacity);

    factory.addIndex(base + 0);
    factory.addIndex(base + 1);
    factory.addIndex(base + 2);
    factory.addIndex(base + 0);
    factory.addIndex(base + 2);
    factory.addIndex(base + 3);

    Mesh mesh         = factory.generateMesh();
    mesh.hasTexture   = true;
    mesh.textureDescriptor = _descriptor;
    return mesh;
}
