/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Compiler
*/

#include "compiler/Compiler.hpp"

#include <condition_variable>
#include <deque>
#include <format>
#include <iostream>
#include <mutex>
#include <thread>

#include "utils/ImageIO.hpp"
#include "vulkan/VulkanHeadlessRenderer.hpp"

VC::Compiler::Compiler(const argparse::ArgumentParser &parser)
    : config({
          .screenWidth = parser.get<float>("--width"),
          .screenHeight = parser.get<float>("--height"),

          .framerate = parser.get<int>("--framerate"),

          .hwEncode = parser.get<bool>("--hwencode"),

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

    if (VC::ImageIO::hasImageExtension(config.outputFile))
        return generateImage(renderer);

    // h264_videotoolbox offloads encoding to the Mac's media engine (lighter on
    // CPU, frees the ~460MB of libx264 buffers), but it has no CRF mode — use
    // -q:v instead (0-100 quality scale, ~65 looks comparable to -crf 23).
    // Quality/bitrate behavior differs from libx264, so it stays opt-in.
    const std::string codecArgs = config.hwEncode
        ? " -c:v h264_videotoolbox"
          " -pix_fmt yuv420p"
          " -q:v 65"
        : " -c:v libx264"
          " -preset veryfast"
          " -pix_fmt yuv420p"
          " -crf 23";

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
            "{}"
            " -movflags +faststart"
            " -loglevel warning"
            " {}",
            (int)config.screenWidth,
            (int)config.screenHeight,
            config.framerate,
            codecArgs,
            config.outputFile
        ).c_str(),
        "w"
    );
    if (!pipe) {
        std::cerr << "Could not start the ffmpeg pipe.\n";
        return 1;
    }

    // Pipelined encode: the blocking fwrite into the FFmpeg pipe (~8 MB/frame,
    // paced by x264) runs on a writer thread behind a small bounded queue, so
    // frame N is encoded while frame N+1 is being built and rendered.
    constexpr size_t        QUEUE_CAP = 4;
    std::deque<cv::Mat>     queue;
    std::mutex              mtx;
    std::condition_variable notFull, notEmpty;
    bool                    producerDone = false;
    bool                    writeFailed  = false;

    std::thread writer([&] {
        while (true) {
            cv::Mat frame;
            {
                std::unique_lock lock(mtx);
                notEmpty.wait(lock, [&] { return !queue.empty() || producerDone; });
                if (queue.empty())
                    break;
                frame = std::move(queue.front());
                queue.pop_front();
            }
            notFull.notify_one();

            size_t bytes = frame.total() * frame.elemSize();
            if (fwrite(frame.data, 1, bytes, pipe) != bytes) {
                std::lock_guard lock(mtx);
                writeFailed = true;
                queue.clear();
                notFull.notify_all();
                break;
            }
        }
    });

    size_t total = _core._nbFrame;
    for (size_t i = 0; i < total; ++i) {
        const auto& meshes = _core.generateMeshes();
        renderer.setMeshes(meshes);

        cv::Mat frame = renderer.readFrame();
        if (!frame.isContinuous())
            frame = frame.clone();

        {
            std::unique_lock lock(mtx);
            notFull.wait(lock, [&] { return queue.size() < QUEUE_CAP || writeFailed; });
            if (writeFailed) {
                std::cerr << std::format("\nFrame {}: ffmpeg pipe write failed.\n", i);
                break;
            }
            queue.push_back(std::move(frame));
        }
        notEmpty.notify_one();

        std::cout << std::format("\rGenerating frame {}/{}...", i + 1, total) << std::flush;
    }

    {
        std::lock_guard lock(mtx);
        producerDone = true;
    }
    notEmpty.notify_all();
    writer.join();

    pclose(pipe);
    if (writeFailed)
        return 1;
    std::cout << std::format("\nDone → {}\n", config.outputFile);
    return 0;
}

int VC::Compiler::generateImage(VulkanHeadlessRenderer& renderer)
{
    const auto& meshes = _core.generateMeshes();
    renderer.setMeshes(meshes);

    cv::Mat frame = renderer.readFrame();
    if (!frame.isContinuous())
        frame = frame.clone();

    if (!VC::ImageIO::write(config.outputFile, frame)) {
        std::cerr << std::format("Failed to write image to {}\n", config.outputFile);
        return 1;
    }

    std::cout << std::format("Done → {}\n", config.outputFile);
    return 0;
}
