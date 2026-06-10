/*
** EPITECH PROJECT, 2026
** video-code
** File description:
** VisualTest — golden-frame & hot-reload visual regression suite
*/

#include "test/VisualTest.hpp"

#include <algorithm>
#include <filesystem>
#include <format>
#include <iostream>
#include <stdexcept>

#include "core/Core.hpp"
#include "utils/Logger.hpp"
#include "vulkan/VulkanHeadlessRenderer.hpp"

namespace fs = std::filesystem;

namespace
{
    // Mean per-pixel BGRA difference. Real renders of the same scene/state are
    // deterministic, so an actual visual regression produces a difference far
    // larger than this — this only absorbs e.g. PNG round-trip rounding.
    constexpr double kMaxMeanDiff = 1.0;

    std::string statusLabel(bool pass)
    {
        return pass
            ? std::format("{}PASS{}", VC::Color::GREEN, VC::Color::RESET)
            : std::format("{}FAIL{}", VC::Color::RED, VC::Color::RESET);
    }

    double meanAbsDiff(const cv::Mat& a, const cv::Mat& b)
    {
        if (a.size() != b.size() || a.type() != b.type())
            return 255.0;

        cv::Mat diff;
        cv::absdiff(a, b, diff);
        cv::Scalar s = cv::mean(diff);
        return (s[0] + s[1] + s[2] + s[3]) / 4.0;
    }

    // Renders frames `frames` (sorted ascending, no duplicates expected) of `core`
    // through `renderer`, by stepping every frame from 0 up to the highest requested
    // index — mirroring Compiler::generateVideo()'s loop so the captured pixels match
    // exactly what `--generate` / the live preview would show.
    std::vector<cv::Mat> captureFrames(VC::Core& core, VC::VulkanHeadlessRenderer& renderer, const std::vector<size_t>& frames)
    {
        size_t               maxFrame = *std::max_element(frames.begin(), frames.end());
        std::vector<cv::Mat> captured(frames.size());

        for (size_t i = 0; i <= maxFrame && i < core._nbFrame; ++i) {
            auto meshes = core.generateMeshes();
            renderer.setMeshes(meshes);

            cv::Mat frame = renderer.readFrame();
            if (!frame.isContinuous())
                frame = frame.clone();

            for (size_t j = 0; j < frames.size(); ++j)
                if (frames[j] == i)
                    captured[j] = frame.clone();
        }

        return captured;
    }

    struct GoldenCase
    {
        std::string         name;
        std::string         scene;
        std::vector<size_t> frames;
    };

    struct ReloadCase
    {
        std::string         name;
        std::string         before;
        std::string         after;
        std::vector<size_t> frames;
    };

    const std::vector<GoldenCase> kGoldenCases = {
        {"shapes",    "test/visual/scenes/shapes.py",    {0}},
        {"text",      "test/visual/scenes/text.py",      {0}},
        {"animation", "test/visual/scenes/animation.py", {0, 10, 25}},
        {"groups",    "test/visual/scenes/groups.py",    {0, 15, 29}},
        {"chess",     "test/visual/scenes/chess.py",     {0, 30, 65, 100, 130}},
        {"gradient",         "test/visual/scenes/gradient.py",         {0}},
        {"gradient-percent", "test/visual/scenes/gradient_percent.py", {0}},
        {"gradient-conic",   "test/visual/scenes/gradient_conic.py",   {0}},
        {"shadow",           "test/visual/scenes/shadow.py",           {0}},
        {"layers",           "test/visual/scenes/layers.py",           {0, 31, 61, 91}},
    };

    const std::vector<ReloadCase> kReloadCases = {
        {"reload-equivalence", "test/visual/scenes/reload_a.py", "test/visual/scenes/reload_b.py", {0, 10, 25}},
    };

    const std::string kGoldenDir = "test/visual/golden";
}

VC::VisualTest::VisualTest(const argparse::ArgumentParser& parser)
    : _parser(parser)
    , _baseConfig({
          // MeshFactory derives its NDC divisor directly from screenWidth/screenHeight,
          // and Metadata's world->pixel transform is hardcoded to a 1920x1080 reference
          // (see config::screenOffset / config::worldToPixelRatio in Metadata.hpp) — so
          // these must match that reference resolution or every shape renders off-screen.
          .screenWidth = 1920.f,
          .screenHeight = 1080.f,
          .framerate = 30,
          .sourceFile = "",
          .outputFile = "",
      })
{
}

std::vector<cv::Mat> VC::VisualTest::renderFrames(const std::string& scenePath, const std::vector<size_t>& frames)
{
    Config config       = _baseConfig;
    config.sourceFile   = scenePath;

    Core core(_parser, config);

    VulkanHeadlessRenderer renderer((uint32_t)config.screenWidth, (uint32_t)config.screenHeight);
    if (!renderer.init())
        throw std::runtime_error("Vulkan headless init failed for " + scenePath);

    core.uploadTextures(
        [&](const cv::Mat& mat) { return renderer.uploadTexture(mat); },
        [&](VkDescriptorSet desc, const cv::Mat& mat) { renderer.updateTexturePixels(desc, mat); }
    );

    return captureFrames(core, renderer, frames);
}

std::vector<cv::Mat> VC::VisualTest::renderFramesAfterReload(
    const std::string& before, const std::string& after, const std::vector<size_t>& frames)
{
    Config config     = _baseConfig;
    config.sourceFile = before;

    Core core(_parser, config);

    VulkanHeadlessRenderer renderer((uint32_t)config.screenWidth, (uint32_t)config.screenHeight);
    if (!renderer.init())
        throw std::runtime_error("Vulkan headless init failed for " + before);

    auto uploadFn   = [&](const cv::Mat& mat) { return renderer.uploadTexture(mat); };
    auto reuploadFn = [&](VkDescriptorSet desc, const cv::Mat& mat) { renderer.updateTexturePixels(desc, mat); };

    core.uploadTextures(uploadFn, reuploadFn);

    // Simulate the user editing the source file and pressing 'R' — exercises
    // Core::reloadSourceFile()'s incremental stack-diffing/rebuild path.
    config.sourceFile = after;
    core.reloadSourceFile();
    core.uploadTextures(uploadFn, reuploadFn);

    return captureFrames(core, renderer, frames);
}

int VC::VisualTest::run(bool updateGolden)
{
    int failures = 0;

    if (updateGolden)
        fs::create_directories(kGoldenDir);

    for (const auto& c : kGoldenCases) {
        std::cout << std::format("{}[visual-test]{} {}{}{}\n", VC::Color::CYAN, VC::Color::RESET, VC::Color::CYAN, c.name, VC::Color::RESET);

        std::vector<cv::Mat> frames;
        try {
            frames = renderFrames(c.scene, c.frames);
        } catch (const std::exception& e) {
            std::cout << std::format("  [{}] {} — {}\n", statusLabel(false), c.name, e.what());
            failures++;
            continue;
        }

        for (size_t j = 0; j < c.frames.size(); ++j) {
            std::string goldenPath = std::format("{}/{}_frame{}.png", kGoldenDir, c.name, c.frames[j]);

            if (updateGolden) {
                cv::imwrite(goldenPath, frames[j]);
                std::cout << std::format("  [{}updated{}] {}\n", VC::Color::YELLOW, VC::Color::RESET, goldenPath);
                continue;
            }

            cv::Mat golden = cv::imread(goldenPath, cv::IMREAD_UNCHANGED);
            if (golden.empty()) {
                std::cout << std::format("  [{}] frame {} — {}no golden image at {} (run with --update-golden first){}\n",
                                         statusLabel(false), c.frames[j], VC::Color::YELLOW, goldenPath, VC::Color::RESET);
                failures++;
                continue;
            }

            double diff = meanAbsDiff(golden, frames[j]);
            bool   pass = diff <= kMaxMeanDiff;
            std::cout << std::format("  [{}] frame {} — mean pixel diff {:.3f} (tolerance {:.1f})\n",
                                     statusLabel(pass), c.frames[j], diff, kMaxMeanDiff);
            if (!pass)
                failures++;
        }
    }

    if (updateGolden) {
        std::cout << std::format("\n{}[visual-test]{} Golden images written to {}/\n", VC::Color::CYAN, VC::Color::RESET, kGoldenDir);
        return 0;
    }

    for (const auto& c : kReloadCases) {
        std::cout << std::format("{}[visual-test]{} {}{}{}\n", VC::Color::CYAN, VC::Color::RESET, VC::Color::CYAN, c.name, VC::Color::RESET);

        std::vector<cv::Mat> expected, actual;
        try {
            expected = renderFrames(c.after, c.frames);
            actual   = renderFramesAfterReload(c.before, c.after, c.frames);
        } catch (const std::exception& e) {
            std::cout << std::format("  [{}] {} — {}\n", statusLabel(false), c.name, e.what());
            failures++;
            continue;
        }

        for (size_t j = 0; j < c.frames.size(); ++j) {
            double diff = meanAbsDiff(expected[j], actual[j]);
            bool   pass = diff <= kMaxMeanDiff;
            std::cout << std::format("  [{}] frame {} — hot-reload vs fresh-load mean diff {:.3f} (tolerance {:.1f})\n",
                                     statusLabel(pass), c.frames[j], diff, kMaxMeanDiff);
            if (!pass)
                failures++;
        }
    }

    std::cout << std::format("\n{}[visual-test]{} {}\n",
                             VC::Color::CYAN, VC::Color::RESET,
                             failures == 0
                                 ? std::format("{}All checks passed.{}", VC::Color::GREEN, VC::Color::RESET)
                                 : std::format("{}{} check(s) FAILED.{}", VC::Color::RED, failures, VC::Color::RESET));
    return failures;
}
