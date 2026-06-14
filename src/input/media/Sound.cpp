/*
** EPITECH PROJECT, 2026
** video-code
** File description:
** Sound
*/

#include "input/media/Sound.hpp"

namespace
{
    double numberOr(const json::object_t& args, const std::string& key, double fallback)
    {
        return args.contains(key) ? args.at(key).get<double>() : fallback;
    }
}

Sound::Sound(json::object_t&& args)
    : AInput(std::move(args))
    , _filepath(_baseArgs.at("filepath").get<std::string>())
    , _volume(numberOr(_baseArgs, "volume", 1.0))
    , _delay(numberOr(_baseArgs, "delay", 0.0))
    , _trimStart(numberOr(_baseArgs, "trimStart", 0.0))
    , _trimEnd(
          _baseArgs.contains("trimEnd") && !_baseArgs.at("trimEnd").is_null()
              ? std::optional<double>(_baseArgs.at("trimEnd").get<double>())
              : std::nullopt
      )
{
}

Mesh Sound::getMesh(const Metadata&, const Config&)
{
    return {};
}
