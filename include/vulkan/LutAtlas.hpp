/*
** EPITECH PROJECT, 2026
** video-code
** File description:
** LutAtlas — parse an Adobe/DaVinci .cube 3D LUT into a flat 2D atlas image.
*/

#pragma once

#include <cctype>
#include <fstream>
#include <opencv2/core.hpp>
#include <sstream>
#include <string>
#include <vector>

// Shared by BOTH renderers (VulkanHeadlessRenderer + VulkanWidget), same
// precedent as EffectResolver.hpp: any code a rendering-behaviour change must
// keep identical between renderers lives in one header, never copy-pasted.
//
// There is NO 3D-texture support anywhere in this codebase (no VK_IMAGE_TYPE_3D
// / sampler3D). Instead of adding that Vulkan surface area, a .cube LUT's blue
// slices are tiled side-by-side into ONE wide 2D image and sampled with the
// exact same 2D texture machinery Image/Video already use (uploadTexture):
//
//   N^3 LUT  ->  atlas of (N*N) x N pixels, BGRA (matches uploadTexture's
//   B8G8R8A8_UNORM upload). Tile b occupies columns [b*N, b*N+N-1] and holds
//   the R-G plane for blue slice b: atlas(y=g, x=b*N + r) = LUT[r,g,b].
//
// The shader reconstructs a graded colour by sampling two adjacent blue tiles
// (b0/b1) with the sampler's bilinear filter doing the R/G interpolation, then
// mix()-ing the two by the blue fraction (trilinear via 2 bilinear taps). See
// assets/shaders/lut/frag.glsl and docs/ADDING_EFFECTS.md (LUT exception).

namespace VC
{
    // Parse a .cube 3D LUT at `filepath` into `atlas` (CV_8UC4, BGRA) and report
    // its edge size `N` in `size`. Returns false if the file is missing, is not
    // a 3D LUT, or the sample count doesn't match N^3.
    //
    // DOMAIN_MIN/MAX are assumed default [0,1] (the common case) and TITLE is
    // ignored — a first-cut parser, documented as such.
    inline bool parseCubeToAtlas(const std::string& filepath, cv::Mat& atlas, int& size)
    {
        std::ifstream file(filepath);
        if (!file.is_open())
            return false;

        int                N = 0;
        std::vector<cv::Vec3f> samples; // in file order: R fastest, then G, then B

        std::string line;
        while (std::getline(file, line)) {
            // Trim leading whitespace.
            size_t s = line.find_first_not_of(" \t\r\n");
            if (s == std::string::npos)
                continue; // blank line
            if (line[s] == '#')
                continue; // comment

            std::istringstream iss(line.substr(s));
            std::string        tok;
            iss >> tok;

            if (tok == "LUT_3D_SIZE") {
                iss >> N;
                if (N > 0)
                    samples.reserve(static_cast<size_t>(N) * N * N);
                continue;
            }
            // Metadata we deliberately ignore (default domain assumed).
            if (tok == "TITLE" || tok == "DOMAIN_MIN" || tok == "DOMAIN_MAX" ||
                tok == "LUT_1D_SIZE" || tok == "LUT_1D_INPUT_RANGE" ||
                tok == "LUT_3D_INPUT_RANGE")
                continue;

            // Otherwise this line should be three floats "R G B". The first
            // token is already in `tok`.
            try {
                float r = std::stof(tok);
                float g = 0.f, b = 0.f;
                if (!(iss >> g >> b))
                    continue; // malformed data line — skip
                samples.emplace_back(r, g, b);
            } catch (const std::exception&) {
                continue; // not a number (unknown keyword) — skip
            }
        }

        if (N <= 0)
            return false;
        if (samples.size() != static_cast<size_t>(N) * N * N)
            return false;

        size = N;

        // Build the flat atlas. Column = b*N + r, row = g. Store BGRA so the
        // B8G8R8A8_UNORM upload lets the shader read texture().rgb as RGB.
        atlas.create(N, N * N, CV_8UC4);
        for (int b = 0; b < N; ++b) {
            for (int g = 0; g < N; ++g) {
                for (int r = 0; r < N; ++r) {
                    // .cube index: R fastest, then G, then B.
                    const cv::Vec3f& c = samples[static_cast<size_t>(r) + static_cast<size_t>(g) * N + static_cast<size_t>(b) * N * N];
                    auto to8 = [](float v) -> uchar {
                        int i = static_cast<int>(v * 255.f + 0.5f);
                        return static_cast<uchar>(i < 0 ? 0 : (i > 255 ? 255 : i));
                    };
                    cv::Vec4b& px = atlas.at<cv::Vec4b>(g, b * N + r);
                    px[0] = to8(c[2]); // B
                    px[1] = to8(c[1]); // G
                    px[2] = to8(c[0]); // R
                    px[3] = 255;
                }
            }
        }
        return true;
    }
}
