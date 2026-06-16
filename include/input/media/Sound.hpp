/*
** EPITECH PROJECT, 2026
** video-code
** File description:
** Sound
*/

#pragma once

#include <optional>
#include <string>

#include "input/AInput.hpp"

// A purely auditory input — no visual geometry (getMesh() is always empty).
// Collected by Compiler::generateVideo() to mux an audio track alongside the
// rendered video.
class Sound final : public AInput
{
public:

    Sound(json::object_t&& args);
    ~Sound() override = default;

    Mesh getMesh(const Metadata& meta, const Config& config) override;

    const std::string& filepath() const { return _filepath; }

    double volume() const { return _volume; }

    double delay() const { return _delay; }

    double trimStart() const { return _trimStart; }

    std::optional<double> trimEnd() const { return _trimEnd; }

private:

    std::string           _filepath;
    double                _volume;
    double                _delay;
    double                _trimStart;
    std::optional<double> _trimEnd;
};
