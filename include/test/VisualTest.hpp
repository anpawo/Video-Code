/*
** EPITECH PROJECT, 2026
** video-code
** File description:
** VisualTest — golden-frame & hot-reload visual regression suite
*/

#pragma once

#include <argparse/argparse.hpp>
#include <opencv2/opencv.hpp>
#include <string>
#include <vector>

#include "core/Config.hpp"

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

        std::vector<cv::Mat> renderFrames(const std::string& scenePath, const std::vector<size_t>& frames);
        std::vector<cv::Mat> renderFramesAfterReload(
            const std::string& before, const std::string& after, const std::vector<size_t>& frames
        );

        const argparse::ArgumentParser& _parser;
        Config                          _baseConfig;
    };
};
