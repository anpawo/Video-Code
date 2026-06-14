/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Compiler
*/

#include "compiler/Compiler.hpp"

#include <cmath>
#include <condition_variable>
#include <deque>
#include <format>
#include <iostream>
#include <mutex>
#include <thread>

#include "input/media/Sound.hpp"
#include "utils/ImageIO.hpp"
#include "vulkan/VulkanHeadlessRenderer.hpp"

namespace
{
    // Extra ffmpeg input arguments (one "-ss .. -to .. -i file" per Sound) and
    // the output arguments that mix/map them onto the encoded video. Empty
    // when there are no Sound inputs — output keeps its current "-an" behavior.
    struct AudioArgs
    {
        std::string inputs; // appended after the rawvideo "-i -"
        std::string output; // appended before the output filename
    };

    AudioArgs buildAudioArgs(const std::vector<std::unique_ptr<IInput>>& inputs)
    {
        std::vector<Sound*> sounds;
        for (const auto& i : inputs)
            if (auto* s = dynamic_cast<Sound*>(i.get()))
                sounds.push_back(s);

        if (sounds.empty())
            return {"", " -an"};

        AudioArgs   result;
        std::string filterComplex;

        for (size_t i = 0; i < sounds.size(); ++i) {
            const Sound* s = sounds[i];

            if (s->trimStart() > 0.0)
                result.inputs += std::format(" -ss {}", s->trimStart());
            if (s->trimEnd())
                result.inputs += std::format(" -to {}", *s->trimEnd());
            result.inputs += std::format(" -i \"{}\"", s->filepath());

            int delayMs = (int)std::llround(s->delay() * 1000.0);
            filterComplex += std::format("[{}:a]volume={},adelay={}|{}[a{}];", i + 1, s->volume(), delayMs, delayMs, i);
        }

        std::string outLabel;
        if (sounds.size() == 1) {
            filterComplex.pop_back(); // drop trailing ';' — single chain, no amix needed
            outLabel = "a0";
        } else {
            for (size_t i = 0; i < sounds.size(); ++i)
                filterComplex += std::format("[a{}]", i);
            filterComplex += std::format("amix=inputs={}:duration=longest:dropout_transition=0[aout]", sounds.size());
            outLabel = "aout";
        }

        result.output = std::format(" -filter_complex \"{}\" -map 0:v -map \"[{}]\" -c:a aac", filterComplex, outLabel);
        return result;
    }
}

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

    AudioArgs audio = buildAudioArgs(_core._inputs);

    FILE* pipe = popen(
        std::format(
            "ffmpeg"
            " -y"
            " -f rawvideo"
            " -pixel_format bgra"
            " -video_size {}x{}"
            " -framerate {}"
            " -i -"
            "{}"
            "{}"
            "{}"
            " -movflags +faststart"
            " -loglevel warning"
            " {}",
            (int)config.screenWidth,
            (int)config.screenHeight,
            config.framerate,
            audio.inputs,
            codecArgs,
            audio.output,
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

    // Scenes are authored at Config::SCENE_FRAMERATE (30fps): _nbFrame and all
    // start/duration values are expressed in that unit. When the requested
    // output framerate differs, resample by mapping each output frame to the
    // nearest scene frame — duplicating frames if framerate > SCENE_FRAMERATE,
    // dropping them if framerate < SCENE_FRAMERATE.
    size_t sceneFrames = _core._nbFrame;
    size_t total = (config.framerate == Config::SCENE_FRAMERATE)
        ? sceneFrames
        : (size_t)std::llround((double)sceneFrames * config.framerate / Config::SCENE_FRAMERATE);

    for (size_t i = 0; i < total; ++i) {
        size_t sceneIndex = (config.framerate == Config::SCENE_FRAMERATE)
            ? i
            : (size_t)std::llround((double)i * Config::SCENE_FRAMERATE / config.framerate);
        if (sceneIndex >= sceneFrames)
            sceneIndex = sceneFrames - 1;
        _core._index = sceneIndex;

        const auto& meshes = _core.generateMeshes();
        renderer.setMeshes(meshes);

        // readFrame() is one-frame pipeline-delayed: it returns the PREVIOUS
        // frame's pixels (empty on the first call) while this frame's GPU
        // work runs asynchronously. The final frame is retrieved via flush()
        // after the loop.
        cv::Mat frame = renderer.readFrame();
        if (!frame.empty()) {
            if (!frame.isContinuous())
                frame = frame.clone();

            std::unique_lock lock(mtx);
            notFull.wait(lock, [&] { return queue.size() < QUEUE_CAP || writeFailed; });
            if (writeFailed) {
                std::cerr << std::format("\nFrame {}: ffmpeg pipe write failed.\n", i);
                break;
            }
            queue.push_back(std::move(frame));
            lock.unlock();
            notEmpty.notify_one();
        }

        std::cout << std::format("\rGenerating frame {}/{}...", i + 1, total) << std::flush;
    }

    {
        cv::Mat frame = renderer.flush();
        if (!frame.empty()) {
            if (!frame.isContinuous())
                frame = frame.clone();

            std::unique_lock lock(mtx);
            notFull.wait(lock, [&] { return queue.size() < QUEUE_CAP || writeFailed; });
            if (!writeFailed)
                queue.push_back(std::move(frame));
            lock.unlock();
            notEmpty.notify_one();
        }
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

    // readFrame() returns the previous (nonexistent) frame's pixels — empty —
    // so the actual frame is retrieved via flush().
    renderer.readFrame();
    cv::Mat frame = renderer.flush();
    if (!frame.isContinuous())
        frame = frame.clone();

    if (!VC::ImageIO::write(config.outputFile, frame)) {
        std::cerr << std::format("Failed to write image to {}\n", config.outputFile);
        return 1;
    }

    std::cout << std::format("Done → {}\n", config.outputFile);
    return 0;
}
