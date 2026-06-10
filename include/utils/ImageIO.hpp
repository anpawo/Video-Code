/*
** EPITECH PROJECT, 2026
** video-code
** File description:
** ImageIO
*/

#pragma once

#include <algorithm>
#include <cctype>
#include <filesystem>
#include <opencv2/opencv.hpp>
#include <string>

namespace VC::ImageIO
{
    inline std::string lowerExtension(const std::string& path)
    {
        std::string ext = std::filesystem::path(path).extension().string();
        std::transform(ext.begin(), ext.end(), ext.begin(), [](unsigned char c) { return std::tolower(c); });
        return ext;
    }

    // Whether `path`'s extension identifies a still-image format (as opposed to video).
    inline bool hasImageExtension(const std::string& path)
    {
        std::string ext = lowerExtension(path);
        return ext == ".png" || ext == ".jpg" || ext == ".jpeg" || ext == ".bmp"
            || ext == ".tiff" || ext == ".tif" || ext == ".webp";
    }

    // Writes a BGRA frame to `path`. PNG/TIFF/WebP keep the alpha channel;
    // other formats (JPEG/BMP/...) are converted to BGR first since
    // cv::imwrite can't write 4-channel data for them.
    inline bool write(const std::string& path, cv::Mat frameBGRA)
    {
        std::string ext = lowerExtension(path);
        if (ext != ".png" && ext != ".tiff" && ext != ".tif" && ext != ".webp")
            cv::cvtColor(frameBGRA, frameBGRA, cv::COLOR_BGRA2BGR);

        return cv::imwrite(path, frameBGRA);
    }
}
