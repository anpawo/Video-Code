/*
** EPITECH PROJECT, 2026
** video-code
** File description:
** VisualTest — golden-frame & hot-reload visual regression suite
*/

#include "test/VisualTest.hpp"

#include <algorithm>
#include <argparse/argparse.hpp>
#include <filesystem>
#include <format>
#include <iostream>
#include <stdexcept>

#include "core/Core.hpp"
#include "core/ScreenSize.hpp"
#include "utils/Logger.hpp"
#include "vulkan/VulkanHeadlessRenderer.hpp"

namespace fs = std::filesystem;

namespace
{
    // MEASURED, and it changes what these two numbers mean: the renderer is
    // byte-deterministic. Regenerating all 87 goldens twice, fifteen minutes and
    // a relink apart, produced 87/87 files identical byte for byte — while 24 of
    // them differ from the goldens committed here.
    //
    // So there is no run-to-run noise for a tolerance to absorb, and the two
    // thresholds below are not noise floors: they are a decision to tolerate 24
    // real, stable, reproducible differences that nobody has diagnosed. The
    // honest long-term target is zero, reached by fixing those 24 — not by
    // tuning a number until they fit under it.
    //
    // Mean per-pixel BGRA difference. Real renders of the same scene/state are
    // deterministic, so an actual visual regression produces a difference far
    // larger than this — this only absorbs e.g. PNG round-trip rounding.
    constexpr double kMaxMeanDiff = 1.0;

    // What one 64x64 tile is allowed to differ by. Calibrated from the goldens
    // and from injected damage, not picked round:
    //
    //     worst tile among the scenes passing today          65.3  (`text`)
    //     erasing a scene's content down to its background    89.5 - 91.5
    //     a 142x142 black square dropped anywhere            102   - 113
    //
    // 80 sits in that gap: nothing that passes today starts failing, and every
    // localised deletion is caught. Deliberately far more permissive per pixel
    // than the frame-wide mean — the point is to notice a LOCAL catastrophe,
    // not to police a gradient.
    //
    // The two tests are complementary and neither is redundant: erasing every
    // glyph of `text` scores 1.201 mean (caught) but only 62.7 per tile
    // (missed), because the damage is spread thin over the whole frame. The
    // mean sees diffuse loss; the tile sees concentrated loss.
    constexpr double kMaxTileDiff = 80.0;

    // Scenes that pass but are not clean, worst first. See the block above:
    // clean means 0.000, so anything here is drift somebody should date.
    struct Drift
    {
        std::string name;
        double      margin;
        double      mean;
        double      tile;
    };

    std::vector<Drift> drifting;

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

    // The worst TILE, beside the mean of the whole frame — because a mean over
    // two million pixels cannot see a feature disappear.
    //
    // Measured against the goldens as they stand: a 142x142 fully black square
    // dropped anywhere in a frame scores 0.992 and PASSES. So does erasing the
    // whole subtitle line (0.487), the cropped element of `crop` (0.548), and
    // the swept element of `lightsweep` (0.592). Every one of those is a
    // feature vanishing, and the gate that exists to catch exactly that says
    // nothing — a small area, however wrong, is divided by the whole frame.
    //
    // A tile is 64x64, so a change confined to one is judged against 4096
    // pixels rather than 2 073 600 — the same defect scores ~500x higher. The
    // frame-wide mean is kept alongside it: broad low-amplitude drift (the
    // `video` / `layers` / `resize` family, 8-10% of pixels at <=8) is real and
    // is what the mean is good at.
    double worstTileDiff(const cv::Mat& a, const cv::Mat& b, int tile = 64)
    {
        if (a.size() != b.size() || a.type() != b.type())
            return 255.0;

        double worst = 0.0;
        for (int y = 0; y < a.rows; y += tile) {
            for (int x = 0; x < a.cols; x += tile) {
                const cv::Rect box(x, y, std::min(tile, a.cols - x), std::min(tile, a.rows - y));
                worst = std::max(worst, meanAbsDiff(a(box), b(box)));
            }
        }
        return worst;
    }

    // Renders frames `frames` (sorted ascending, no duplicates expected) of `core`
    // through `renderer`, by stepping every frame from 0 up to the highest requested
    // index — mirroring Compiler::generateVideo()'s loop so the captured pixels match
    // exactly what `--generate` / the live preview would show.
    std::vector<cv::Mat> captureFrames(VC::Core& core, VC::VulkanHeadlessRenderer& renderer, const std::vector<size_t>& frames)
    {
        size_t               maxFrame = *std::max_element(frames.begin(), frames.end());
        std::vector<cv::Mat> captured(frames.size());

        auto store = [&](size_t frameIdx, cv::Mat mat) {
            if (!mat.isContinuous())
                mat = mat.clone();
            for (size_t j = 0; j < frames.size(); ++j)
                if (frames[j] == frameIdx)
                    captured[j] = mat.clone();
        };

        // readFrame() is one-frame pipeline-delayed: it returns frame (i-1)'s
        // pixels (empty on the first call). The final submitted frame is
        // retrieved via flush() after the loop.
        for (size_t i = 0; i <= maxFrame && i < core._nbFrame; ++i) {
            const auto& meshes = core.generateMeshes();
            renderer.setMeshes(meshes);
            renderer.setBackgroundColor(core._bgColor);

            cv::Mat frame = renderer.readFrame();
            if (!frame.empty())
                store(i - 1, frame);
        }

        if (core._nbFrame > 0) {
            cv::Mat last = renderer.flush();
            if (!last.empty())
                store(std::min(maxFrame, core._nbFrame - 1), last);
        }

        return captured;
    }

    struct GoldenCase
    {
        std::string         name;
        std::string         scene;
        std::vector<size_t> frames;
        // Resolution for this case. 0 = the suite's base (1920x1080). Lives
        // here rather than in the scene because --width/--height are the only
        // way to set a resolution — a scene has no say, by design.
        int width = 0;
        int height = 0;
    };

    struct ReloadCase
    {
        std::string         name;
        std::string         before;
        std::string         after;
        std::vector<size_t> frames;
    };

    const std::vector<GoldenCase> kGoldenCases = {
        {"shapes", "test/visual/scenes/shapes.py", {0}},
        {"text", "test/visual/scenes/text.py", {0}},
        {"text-stroke", "test/visual/scenes/text_stroke.py", {0}},
        {"animation", "test/visual/scenes/animation.py", {0, 10, 25}},
        {"groups", "test/visual/scenes/groups.py", {0, 15, 29}},
        {"stateful-group-scale", "test/visual/scenes/stateful_group_scale.py", {0, 15, 29}},
        {"chess", "test/visual/scenes/chess.py", {0, 30, 65, 100, 130}},
        {"gradient", "test/visual/scenes/gradient.py", {0}},
        {"gradient-percent", "test/visual/scenes/gradient_percent.py", {0}},
        {"gradient-conic", "test/visual/scenes/gradient_conic.py", {0}},
        {"shadow", "test/visual/scenes/shadow.py", {0}},
        {"crop", "test/visual/scenes/crop.py", {0}},
        {"curve", "test/visual/scenes/curve.py", {0, 6, 10}},
        {"lightsweep", "test/visual/scenes/lightsweep.py", {0, 15, 29}},
        {"lightsweep-group", "test/visual/scenes/lightsweep_group.py", {7, 15, 22}},
        {"layers", "test/visual/scenes/layers.py", {0, 31, 61, 91}},
        {"text-gradient", "test/visual/scenes/text_gradient.py", {0, 11, 22, 33}},
        {"gradient-holes", "test/visual/scenes/gradient_holes.py", {0}},
        {"video", "test/visual/scenes/video.py", {0}},
        {"image-shape", "test/visual/scenes/image_shape.py", {0}},
        {"uv-mapping", "test/visual/scenes/uv_mapping.py", {0}},
        {"resize", "test/visual/scenes/resize.py", {0, 15, 29}},
        {"svg", "test/visual/scenes/svg.py", {0}},
        {"mathtex", "test/visual/scenes/mathtex.py", {0}},
        {"subtitles", "test/visual/scenes/subtitles.py", {30}},
        {"markdown", "test/visual/scenes/markdown.py", {0}},
        {"sound", "test/visual/scenes/sound.py", {0}},
        {"effect-shaders", "test/visual/scenes/effect_shaders.py", {0, 15}},
        {"effect-templates", "test/visual/scenes/effect_templates.py", {0, 7, 15, 29}},
        {"easings", "test/visual/scenes/easings.py", {8, 15, 29}},
        {"effect-shaders2", "test/visual/scenes/effect_shaders2.py", {0, 15}},
        {"effect-templates2", "test/visual/scenes/effect_templates2.py", {0, 7, 15, 29}},
        {"effect-shaders3", "test/visual/scenes/effect_shaders3.py", {0}},
        {"effect-templates3", "test/visual/scenes/effect_templates3.py", {0, 7, 15, 29}},
        {"effect-shaders4", "test/visual/scenes/effect_shaders4.py", {0}},
        {"transitions", "test/visual/scenes/transitions.py", {0, 8, 15}},
        {"blend-modes", "test/visual/scenes/blend_modes.py", {0}},
        {"glow", "test/visual/scenes/glow.py", {0}},
        {"matte", "test/visual/scenes/matte.py", {0}},
        {"lut", "test/visual/scenes/lut.py", {0}},
        {"adjustment-layer", "test/visual/scenes/adjustment_layer.py", {0}},
        // Frame 15 too: silk is time-driven, so a stuck clock (elapsed frames
        // never reaching the GLSL) would pass a frame-0-only check.
        {"silk", "test/visual/scenes/silk.py", {0, 15}},
        // Two frames: three of the four Space modes differ only over time —
        // what the pattern does while its host scales IS the check.
        {"shader-space", "test/visual/scenes/shader_space.py", {0, 29}},
        {"background", "test/visual/scenes/background.py", {0}},
        // Portrait: proves the world->pixel transform follows the resolution.
        {"aspect-portrait", "test/visual/scenes/aspect_portrait.py", {0}, 1080, 1920},
        // Also portrait: SplitView stacking itself because the world is taller
        // than it is wide (Split.AUTO).
        {"split-rows", "test/visual/scenes/split_rows.py", {0}, 1080, 1920},
    };

    const std::vector<ReloadCase> kReloadCases = {
        {"reload-equivalence", "test/visual/scenes/reload_a.py", "test/visual/scenes/reload_b.py", {0, 10, 25}},
    };

    const std::string kGoldenDir = "test/visual/golden";
}

VC::VisualTest::VisualTest(const argparse::ArgumentParser& parser)
    : _parser(parser)
    , _baseConfig({
          // The goldens are 1920x1080, so the suite pins the resolution instead of
          // reading constants.py: editing the project default must not move every
          // golden. A scene declaring its own size still gets it (configFor).
          .screenWidth = 1920.f,
          .screenHeight = 1080.f,
          .framerate = 30,
          .sourceFile = "",
          .outputFile = "",
      })
{
    // MeshFactory derives its NDC divisor from screenWidth/screenHeight while
    // Metadata's world->pixel transform reads config::screenOffset — the two have
    // to agree or every shape renders off-center.
    applyScreenSize(_baseConfig.screenWidth, _baseConfig.screenHeight);
}

Config VC::VisualTest::configFor(const std::string& scenePath, int width, int height)
{
    Config config = _baseConfig;
    config.sourceFile = scenePath;

    // A case may pin its own resolution (portrait cases do); everything else
    // renders at the suite's base, which is what the goldens were written at.
    if (width > 0 && height > 0) {
        config.screenWidth = (float)width;
        config.screenHeight = (float)height;
    }
    // Reapplied per scene because the world->pixel transform it drives is
    // process-global, and the previous case may have moved it.
    applyScreenSize(config.screenWidth, config.screenHeight);

    return config;
}

std::vector<cv::Mat> VC::VisualTest::renderFrames(
    const std::string& scenePath, const std::vector<size_t>& frames, int width, int height
)
{
    Config config = configFor(scenePath, width, height);

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
    const std::string& before, const std::string& after, const std::vector<size_t>& frames
)
{
    Config config = configFor(before, 0, 0);

    Core core(_parser, config);

    VulkanHeadlessRenderer renderer((uint32_t)config.screenWidth, (uint32_t)config.screenHeight);
    if (!renderer.init())
        throw std::runtime_error("Vulkan headless init failed for " + before);

    auto uploadFn = [&](const cv::Mat& mat) { return renderer.uploadTexture(mat); };
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
            frames = renderFrames(c.scene, c.frames, c.width, c.height);
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
                std::cout << std::format("  [{}] frame {} — {}no golden image at {} (run with --update-golden first){}\n", statusLabel(false), c.frames[j], VC::Color::YELLOW, goldenPath, VC::Color::RESET);
                failures++;
                continue;
            }

            double diff = meanAbsDiff(golden, frames[j]);
            double tile = worstTileDiff(golden, frames[j]);
            bool   pass = diff <= kMaxMeanDiff && tile <= kMaxTileDiff;
            std::cout << std::format("  [{}] frame {} — mean {:.3f} (max {:.1f}) · worst 64px tile {:.3f} (max {:.1f})\n", statusLabel(pass), c.frames[j], diff, kMaxMeanDiff, tile, kMaxTileDiff);
            // Kept even when it passes: a threshold you cannot watch being
            // approached is a threshold that breaks by surprise. `text` sits at
            // 65.3 of 80 and is declared nowhere — the second worst tile in the
            // suite, worse than three of the four failures that ARE declared.
            if (pass && (diff > 0.0 || tile > 0.0))
                drifting.push_back({c.name, tile / kMaxTileDiff, diff, tile});
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
            actual = renderFramesAfterReload(c.before, c.after, c.frames);
        } catch (const std::exception& e) {
            std::cout << std::format("  [{}] {} — {}\n", statusLabel(false), c.name, e.what());
            failures++;
            continue;
        }

        for (size_t j = 0; j < c.frames.size(); ++j) {
            double diff = meanAbsDiff(expected[j], actual[j]);
            double tile = worstTileDiff(expected[j], actual[j]);
            bool   pass = diff <= kMaxMeanDiff && tile <= kMaxTileDiff;
            std::cout << std::format("  [{}] frame {} — hot-reload vs fresh-load: mean {:.3f} · worst tile {:.3f}\n", statusLabel(pass), c.frames[j], diff, tile);
            if (!pass)
                failures++;
        }
    }

    // Said out loud even when everything passes, because this is exactly what
    // went unnoticed: `matte` failed for a month while `make check` reported
    // only failures it did not already expect, and seven more scenes drift
    // under the thresholds with nothing anywhere recording that they do.
    if (!drifting.empty()) {
        std::sort(drifting.begin(), drifting.end(), [](const Drift& a, const Drift& b) { return a.margin > b.margin; });
        std::cout << std::format("\n{}[visual-test]{} passing, but not clean — a clean render is 0.000:\n", VC::Color::CYAN, VC::Color::RESET);
        for (const Drift& d : drifting)
            std::cout << std::format("  {:<18} mean {:6.3f}  tile {:6.3f}  ({:.0f}% of the tile budget)\n", d.name, d.mean, d.tile, d.margin * 100.0);
    }

    std::cout << std::format("\n{}[visual-test]{} {}\n", VC::Color::CYAN, VC::Color::RESET, failures == 0 ? std::format("{}All checks passed.{}", VC::Color::GREEN, VC::Color::RESET) : std::format("{}{} check(s) FAILED.{}", VC::Color::RED, failures, VC::Color::RESET));
    // 0 or 1, never the count. A POSIX exit code is truncated mod 256, so a
    // suite that grew to 256 simultaneous failures would have exited 0 —
    // "everything broke" and "nothing broke" being the same byte. The count is
    // printed on the line above, which is where a human reads it.
    return failures == 0 ? 0 : 1;
}
