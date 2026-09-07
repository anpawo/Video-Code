#pragma once

#include <memory>
#include <optional>
#include <string>
#include <utility>
#include <vector>

#include "input/IInput.hpp"

// The scene's sound as one ffmpeg graph — the SAME graph for the file the
// render writes and for the WAV the editor plays. One mixer, so what is heard
// in the preview is what comes out of the export; a second mix would be a
// preview that lies.
namespace VC::Audio
{
    // Extra ffmpeg input arguments (one "-ss .. -to .. -i file" per track) and
    // the output arguments that mix/map them onto the encoded video. Empty
    // when nothing carries sound — output keeps its current "-an" behaviour.
    struct AudioArgs
    {
        std::string inputs; // appended after the rawvideo "-i -"
        std::string output; // appended before the output filename
        // How many `-i` the inputs above are. Anything appended AFTER them is
        // input 1 + this, and the audio filter already counts on the video
        // being input 0 — so a chapter file added at the end shifts nothing.
        size_t count = 0;
    };

    // The graph alone, before any container is decided.
    struct AudioGraph
    {
        std::vector<std::string> inputArgs; // "-ss", "0.5", "-i", "file", … one argument each
        std::string              inputs;    // the same, as one command-line string
        std::string              filter;    // the filter_complex text, unquoted
        std::string              label;     // what to -map: a0, aout or arange
        size_t                   count = 0; // tracks — 0 means silence
    };

    // `firstInput` is the ffmpeg input index of the first sound: 1 at the
    // render, where the picture is input 0; 0 at the preview, which has none.
    AudioGraph buildAudioGraph(const std::vector<std::unique_ptr<IInput>>& inputs, std::optional<std::pair<double, double>> window, size_t frames, size_t firstInput);

    AudioArgs buildAudioArgs(const std::vector<std::unique_ptr<IInput>>& inputs, const std::string& audioCodec, std::optional<std::pair<double, double>> window, size_t frames);
} // namespace VC::Audio
