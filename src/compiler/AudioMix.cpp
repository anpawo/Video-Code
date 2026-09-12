#include "compiler/AudioMix.hpp"

#include <cmath>
#include <cstdio>
#include <format>
#include <iostream>

#include "core/Config.hpp"
#include "input/media/Sound.hpp"
#include "input/media/Video.hpp"

namespace VC::Audio
{
    // A video with no audio stream must not be mapped: ffmpeg refuses the
    // whole mux over a "[3:a]" that matches nothing, picture included.
    bool hasAudioStream(const std::string& filepath)
    {
        FILE* p = popen(std::format("ffprobe -v error -select_streams a -show_entries stream=codec_type -of csv=p=0 \"{}\"", filepath).c_str(), "r");
        if (!p)
            return false;
        char buf[16];
        bool any = fgets(buf, sizeof buf, p) != nullptr;
        pclose(p);
        return any;
    }

    // A Video's own track. Its picture starts where the script put the clip,
    // so the sound is delayed to meet it — the same `adelay` a Sound carries,
    // written after the retime so the milliseconds are output time. Keeping
    // the audio between the cut ranges and butting the pieces together is what
    // leaves it under the frames that are actually shown. atrim over
    // asplit rather than one aselect expression, because aselect on audio
    // drops nothing at all in ffmpeg 8.0.1 (measured: `gte(t,1)` kept 2.005 s
    // of 2.005). The picture is nearest-frame at one source frame per scene
    // frame, so a source not at the scene's rate plays at SCENE_FRAMERATE/fps
    // speed and the sound follows with atempo.
    // ponytail: atempo floors at 0.5, so a source above 60 fps fails the mux;
    // neither speed ramps nor a paused VIDEOS clock (freeze) reach the sound.
    std::string videoAudioChain(const Video& v, size_t ffmpegInput, size_t track)
    {
        double      fps = v.sourceFps() > 0.0 ? v.sourceFps() : Config::SCENE_FRAMERATE;
        std::string tempo = fps != Config::SCENE_FRAMERATE ? std::format(",atempo={}", Config::SCENE_FRAMERATE / fps) : "";

        if (v._origin > 0) {
            long long ms = std::llround(static_cast<double>(v._origin) * 1000.0 / Config::SCENE_FRAMERATE);
            tempo += std::format(",adelay={0}|{0}", ms);
        }

        if (v.cuts().empty())
            return std::format("[{}:a]anull{}[a{}];", ffmpegInput, tempo, track);

        // Kept ranges in source seconds; an end of -1 runs to the end of the file.
        std::vector<std::pair<double, double>> keep;
        size_t                                 at = 0;
        for (const auto& [start, end] : v.cuts()) {
            if (start > at)
                keep.push_back({at / fps, start / fps});
            at = end;
        }
        if (at < v._nbFrame)
            keep.push_back({at / fps, -1.0});

        auto trim = [&](const std::pair<double, double>& range) {
            return std::format("atrim=start={}{},asetpts=PTS-STARTPTS", range.first, range.second < 0 ? "" : std::format(":end={}", range.second));
        };

        if (keep.empty())
            return std::format("[{}:a]atrim=end=0{}[a{}];", ffmpegInput, tempo, track);
        if (keep.size() == 1)
            return std::format("[{}:a]{}{}[a{}];", ffmpegInput, trim(keep[0]), tempo, track);

        std::string chain = std::format("[{}:a]asplit={}", ffmpegInput, keep.size());
        for (size_t k = 0; k < keep.size(); ++k)
            chain += std::format("[s{}_{}]", track, k);
        chain += ";";
        for (size_t k = 0; k < keep.size(); ++k)
            chain += std::format("[s{}_{}]{}[k{}_{}];", track, k, trim(keep[k]), track, k);
        for (size_t k = 0; k < keep.size(); ++k)
            chain += std::format("[k{}_{}]", track, k);
        chain += std::format("concat=n={}:v=0:a=1{}[a{}];", keep.size(), tempo, track);
        return chain;
    }

    // `window` is the rendered stretch in seconds when --from/--to narrowed
    // it. The whole timeline is still mixed as one, with every delay and cut
    // above kept absolute, and the window is cut out of the RESULT: that is
    // what keeps a sound that began before --from at the right moment, heard
    // from where the range enters it, instead of re-delaying each track and
    // trimming each file by hand. Decoding the part before the window costs
    // audio decode time, which is nothing next to one rendered frame.
    // The gain a scene CLAIMED, frame by frame, as one ffmpeg expression.
    //
    // `Sound(volume=0.8)` is a constructor argument and was the only volume the
    // mux ever read. But `music.over(duration=1.5).volume = 0` is the same
    // sentence every visual property answers to, and it lands on the timeline
    // as a per-frame claim exactly like a fade does — the renderer just threw
    // it away, so a fade-out written that way came out at full level with
    // nothing said. The claims are per FRAME, so the expression is too: one
    // term per run of equal frames, each one holding for the frames it covers.
    //
    // "" when the scene claimed nothing but the constructor's value — a plain
    // `volume=0.8` reads better in the command and in a log.
    std::string volumeExpression(const IInput& input, double fallback, size_t frames)
    {
        std::vector<std::pair<size_t, double>> runs; // first frame → value
        for (size_t frame = 0; frame < frames; ++frame) {
            const json::object_t& args = const_cast<IInput&>(input).getMetadata(frame).args();
            const auto            found = args.find("volume");
            const double          level = found != args.end() && found->second.is_number()
                                              ? found->second.get<double>()
                                              : fallback;
            if (runs.empty() || runs.back().second != level)
                runs.emplace_back(frame, level);
        }
        if (runs.size() <= 1)
            return "";

        std::string expression;
        for (size_t i = 0; i < runs.size(); ++i) {
            const double from = (double)runs[i].first / Config::SCENE_FRAMERATE;
            if (!expression.empty())
                expression += "+";
            // The last run holds to the end of the track, which may be longer
            // than the scene: a sound that outlives the picture keeps the level
            // it was left at rather than dropping to nothing.
            expression += i + 1 < runs.size()
                              ? std::format("{:.6g}*gte(t,{:.6f})*lt(t,{:.6f})", runs[i].second, from, (double)runs[i + 1].first / Config::SCENE_FRAMERATE)
                              : std::format("{:.6g}*gte(t,{:.6f})", runs[i].second, from);
        }

        // A ramp is tens of terms; a scene that claims a different level on
        // every frame of a long track is thousands, and the command line is
        // what breaks. Said out loud rather than quietly coarsened.
        if (expression.size() > 32000) {
            std::cerr << std::format(
                "video-code: the volume claimed on this sound changes {} times — too many for one filter, so the average is used instead.\n",
                runs.size()
            );
            double total = 0;
            for (const auto& [frame, level] : runs)
                total += level;
            return std::format("{:.6g}", total / (double)runs.size());
        }
        return expression;
    }

    AudioGraph buildAudioGraph(const std::vector<std::unique_ptr<IInput>>& inputs, std::optional<std::pair<double, double>> window, size_t frames, size_t firstInput)
    {
        AudioGraph graph;
        size_t     tracks = 0;

        auto arg = [&graph](std::string one) {
            graph.inputs += " " + one;
            graph.inputArgs.push_back(std::move(one));
        };
        auto file = [&graph](const std::string& path) {
            graph.inputs += std::format(" -i \"{}\"", path);
            graph.inputArgs.push_back("-i");
            graph.inputArgs.push_back(path);
        };

        for (const auto& i : inputs) {
            if (auto* s = dynamic_cast<Sound*>(i.get())) {
                if (s->trimStart() > 0.0) {
                    arg("-ss");
                    arg(std::format("{}", s->trimStart()));
                }
                if (s->trimEnd()) {
                    arg("-to");
                    arg(std::format("{}", *s->trimEnd()));
                }
                file(s->filepath());

                int delayMs = (int)std::llround(s->delay() * 1000.0);
                // The delay comes FIRST so the gain expression is written in
                // the scene's own clock: after `adelay`, `t` is the moment the
                // author sees on the timeline, which is what their claim said.
                const std::string claimed = volumeExpression(*i, s->volume(), frames);
                graph.filter += claimed.empty()
                                    ? std::format("[{}:a]volume={},adelay={}|{}[a{}];", tracks + firstInput, s->volume(), delayMs, delayMs, tracks)
                                    : std::format("[{}:a]adelay={}|{},volume=volume='{}':eval=frame[a{}];", tracks + firstInput, delayMs, delayMs, claimed, tracks);
                ++tracks;
            } else if (auto* v = dynamic_cast<Video*>(i.get()); v && hasAudioStream(v->filepath())) {
                file(v->filepath());
                graph.filter += videoAudioChain(*v, tracks + firstInput, tracks);
                ++tracks;
            }
        }

        if (tracks == 0)
            return graph;

        graph.label = "a0"; // single chain, no amix needed
        if (tracks > 1) {
            for (size_t i = 0; i < tracks; ++i)
                graph.filter += std::format("[a{}]", i);
            // normalize=0: amix otherwise divides every track by the number of
            // tracks and scales the rest back up as each one ends — so a voice
            // over music played the music at HALF its claimed level while the
            // voice lasted, then let it back up when the voice stopped, which is
            // a duck turned inside out. Measured: 0.6 claimed came out as 0.3
            // beside a voice and 0.6 after it. A level claimed is the level
            // mixed; what sums past 1.0 clips, which is what the author asked for.
            graph.filter += std::format("amix=inputs={}:duration=longest:dropout_transition=0:normalize=0[aout];", tracks);
            graph.label = "aout";
        }
        if (window) {
            graph.filter += std::format("[{}]atrim=start={}:end={},asetpts=PTS-STARTPTS[arange];", graph.label, window->first, window->second);
            graph.label = "arange";
        }
        graph.filter.pop_back(); // every chain ends in ';'
        graph.count = tracks;
        return graph;
    }

    AudioArgs buildAudioArgs(const std::vector<std::unique_ptr<IInput>>& inputs, const std::string& audioCodec, std::optional<std::pair<double, double>> window, size_t frames)
    {
        const AudioGraph graph = buildAudioGraph(inputs, window, frames, 1);
        if (graph.count == 0)
            return {"", " -an", 0};
        return {graph.inputs, std::format(" -filter_complex \"{}\" -map 0:v -map \"[{}]\" -c:a {}", graph.filter, graph.label, audioCodec), graph.count};
    }
} // namespace VC::Audio
