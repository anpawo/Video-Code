/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Compiler
*/

#include "compiler/Compiler.hpp"

#include <chrono>
#include <cmath>
#include <condition_variable>
#include <deque>
#include <format>
#include <iostream>
#include <mutex>
#include <string>
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

    // ── Progress bar (pip-style) ──────────────────────────────────────────────

    constexpr const char* kReset = "\033[0m";
    constexpr const char* kGreenB = "\033[1;32m";
    constexpr const char* kDim = "\033[2m";
    constexpr const char* kBold = "\033[1m";

    std::string rep(const char* s, int n)
    {
        std::string out;
        out.reserve(std::string(s).size() * (size_t)n);
        for (int k = 0; k < n; ++k) out += s;
        return out;
    }

    // Red (0%) → yellow (50%) → green (100%) via 24-bit ANSI RGB.
    std::string barColor(double frac)
    {
        frac = frac < 0.0 ? 0.0 : frac > 1.0 ? 1.0
                                             : frac;
        int r, g;
        if (frac <= 0.5) {
            r = 210;
            g = (int)(frac * 2.0 * 180);
        } else {
            r = (int)((1.0 - frac) * 2.0 * 210);
            g = 180;
        }
        return std::format("\033[38;2;{};{};0m", r, g);
    }

    // Overwrites the current terminal line with the progress bar.
    void printProgress(size_t done, size_t total, double /*elapsed*/)
    {
        constexpr int W = 40;
        double        frac = total > 0 ? (double)done / (double)total : 0.0;
        int           filled = std::min(W, (int)(frac * W + 0.5));
        int           empty = W - filled;
        int           pct = std::min(100, (int)(frac * 100 + 0.5));

        std::string bar = "   ";
        bar += barColor(frac);
        bar += rep("━", filled);
        if (empty > 0) {
            bar += kDim;
            bar += rep("╌", empty);
        }
        bar += kReset;
        bar += std::format("  {:3d}%  {}/{} frames", pct, done, total);
        std::cout << "\r" << bar << std::flush;
    }
}

VC::Compiler::Compiler(const argparse::ArgumentParser& parser)
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
        )
            .c_str(),
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
    bool                    writeFailed = false;

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

    // Header line — printed once; ETA is appended in-place after the first frame.
    auto fmtDur = [](double secs) -> std::string {
        return secs < 60.0
            ? std::format("{:.1f}s", secs)
            : std::format("{:d}:{:02d} min", (int)secs / 60, (int)secs % 60);
    };
    double      durSecs = config.framerate > 0 ? (double)total / config.framerate : 0.0;
    std::string headerBase = std::string(kBold) + "Generating" + kReset + "  " + config.outputFile + "   " + kDim + std::format("{}x{} · {} fps · {} · {} frames", (int)config.screenWidth, (int)config.screenHeight, config.framerate, fmtDur(durSecs), total) + kReset;
    std::cout << headerBase << "\n";

    auto   t0      = std::chrono::steady_clock::now();
    double etaSecs = -1.0; // set once after the first frame, never updated again

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

        double elapsed = std::chrono::duration<double>(std::chrono::steady_clock::now() - t0).count();
        if (etaSecs < 0.0 && elapsed > 0.0) {
            etaSecs = elapsed * (double)total; // first frame time × total
            // Go up one line and reprint the header with ETA appended.
            std::cout << "\033[1A\r\033[2K"
                      << headerBase << kDim << " · eta " << fmtDur(etaSecs)
                      << kReset << "\n";
        }
        printProgress(i + 1, total, elapsed);
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

    double totalElapsed = std::chrono::duration<double>(std::chrono::steady_clock::now() - t0).count();

    std::string doneBar = std::string(kGreenB) + "✓" + kReset + "  ";
    doneBar += barColor(1.0);
    doneBar += rep("━", 40);
    doneBar += kReset;
    doneBar += std::format("  100%  {:.1f}s", totalElapsed);
    doneBar += "                    "; // clear leftover frame-count text
    std::cout << "\r" << doneBar << "\n";
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

    std::cout << kGreenB << "✓" << kReset << "  " << config.outputFile << "\n";
    return 0;
}
