/*
** EPITECH PROJECT, 2026
** video-code
** File description:
** VisualTest — golden-frame & hot-reload visual regression suite
*/

#pragma once

#include <opencv2/opencv.hpp>
#include <string>
#include <vector>

#include "core/Config.hpp"

// argparse is a COMMAND-LINE parser, and it was reaching five headers through
// this one — 1381 of the 1754 include events of a 75-line ScreenSize.cpp. Every
// use here is by reference, so a forward declaration is all a header needs; the
// definition belongs to the .cpp files that actually read a flag.
namespace argparse
{
    class ArgumentParser;
}

namespace VC
{
    // -------------------------------------------------------------------------
    // VisualTest
    //   Renders a fixed set of scenes headlessly (VulkanHeadlessRenderer, no
    //   ffmpeg) and compares the resulting frames against golden PNGs stored in
    //   test/visual/golden/. Also checks that hot-reloading from one scene to
    //   another (Core::reloadSourceFile) produces pixel-identical output to a
    //   fresh load of the destination scene — the "reload equivalence" check.
    //
    //   Run with `--visual-test`; pass `--update-golden` to (re)write the
    //   golden images instead of comparing against them.
    // -------------------------------------------------------------------------
    class VisualTest
    {
    public:

        explicit VisualTest(const argparse::ArgumentParser& parser);

        // Runs every registered case, printing PASS/FAIL per check.
        // Returns the number of failed checks (0 = everything passed).
        int run(bool updateGolden);

    private:

        // The Config a case renders under — _baseConfig unless the case pins its
        // own size. Also (re)points the world->pixel transform at it.
        Config configFor(const std::string& scenePath, int width, int height);

        std::vector<cv::Mat> renderFrames(
            const std::string& scenePath, const std::vector<size_t>& frames, int width = 0, int height = 0
        );
        std::vector<cv::Mat> renderFramesAfterReload(
            const std::string& before, const std::string& after, const std::vector<size_t>& frames
        );

        const argparse::ArgumentParser& _parser;
        Config                          _baseConfig;
    };
};
