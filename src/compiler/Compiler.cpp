/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Compiler
*/

#include "compiler/Compiler.hpp"

#include <format>
#include <iostream>

#include "vulkan/VulkanHeadlessRenderer.hpp"

VC::Compiler::Compiler(const argparse::ArgumentParser &parser)
    : config({
          .screenWidth = parser.get<float>("--width"),
          .screenHeight = parser.get<float>("--height"),

          .framerate = parser.get<int>("--framerate"),

          .sourceFile = parser.get("--file"),
          .outputFile = parser.get("--generate"),
      })
    , _core(parser, config)
{
}

VC::Compiler::~Compiler() = default;

int VC::Compiler::generateVideo()
{
    VulkanHeadlessRenderer renderer(
        (uint32_t)config.screenWidth,
        (uint32_t)config.screenHeight
    );

    if (!renderer.init()) {
        std::cerr << "Vulkan headless init failed.\n";
        return 1;
    }

    _core.uploadTextures(
        [&](const cv::Mat& mat) { return renderer.uploadTexture(mat); },
        [&](VkDescriptorSet desc, const cv::Mat& mat) { renderer.updateTexturePixels(desc, mat); }
    );

    FILE* pipe = popen(
        std::format(
            "ffmpeg"
            " -y"
            " -f rawvideo"
            " -pixel_format bgra"
            " -video_size {}x{}"
            " -framerate {}"
            " -an"
            " -i -"
            " -c:v libx264"
            " -preset veryfast"
            " -pix_fmt yuv420p"
            " -crf 23"
            " -movflags +faststart"
            " -loglevel warning"
            " {}",
            (int)config.screenWidth,
            (int)config.screenHeight,
            config.framerate,
            config.outputFile
        ).c_str(),
        "w"
    );
    if (!pipe) {
        std::cerr << "Could not start the ffmpeg pipe.\n";
        return 1;
    }

    size_t total = _core._nbFrame;
    for (size_t i = 0; i < total; ++i) {
        auto meshes = _core.generateMeshes();
        renderer.setMeshes(meshes);

        cv::Mat frame = renderer.readFrame();
        if (!frame.isContinuous())
            frame = frame.clone();

        size_t bytes   = frame.total() * frame.elemSize();
        size_t written = fwrite(frame.data, 1, bytes, pipe);
        if (written != bytes) {
            std::cerr << std::format("Frame {}: wrote {}/{} bytes.\n", i, written, bytes);
            pclose(pipe);
            return 1;
        }

        std::cout << std::format("\rGenerating frame {}/{}...", i + 1, total) << std::flush;
    }

    pclose(pipe);
    std::cout << std::format("\nDone → {}\n", config.outputFile);
    return 0;
}
