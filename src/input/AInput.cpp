/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Input
*/

#include "input/AInput.hpp"

#include <cstddef>

#include "input/IInput.hpp"
#include "input/Metadata.hpp"
#include "shader/IVertexShader.hpp"
#include "shader/ShaderFactory.hpp"

AInput::AInput(json::object_t&& args)
    : _baseArgsPtr(std::make_shared<const json::object_t>(std::move(args)))
    , _baseArgs(*_baseArgsPtr)
{
}

void AInput::resetModifications()
{
    _hasArgsShader = false;
    _effects.clear();
    _effectTimeline.clear();
    _metas = {Metadata{.argsPtr = _baseArgsPtr}};
}

void AInput::add(const std::string& name, const std::string& type, json::object_t&& args)
{
    size_t start = args.at("start");
    size_t duration = args.at("duration");

    if (type == "VertexShader") {
        VertexShader t = getTransformFromString.at(name);

        if (start >= _metas.size()) {
            Metadata meta = _metas.back();
            _metas.resize(start + 1, meta);
        }

        if (t == VertexShader::Args)
            _hasArgsShader = true;
        getMetadataFromArgs(t, args, _metas[start]);

    } else if (type == "FragmentShader") {
        ///< If a shader is single frame, it will ignore the index argument when called.
        ///< otherwise, it will use it. e.g. Opacity, LightSweep
        ///< that's why we duplicate the index of shader over duration.
        _effects.push_back(transformation.at(name)(args));

        size_t effectIndex = _effects.size() - 1;

        if (_effectTimeline.size() < start + duration) {
            _effectTimeline.resize(start + duration);
        }

        for (size_t i = start; i < start + duration; i++) {
            _effectTimeline[i].push_back(effectIndex);
        }
    }
}

std::vector<ActiveEffect> AInput::getActiveEffectsAtFrame(size_t frame) const
{
    if (frame >= _effectTimeline.size())
        return {};

    std::vector<ActiveEffect> result;
    for (size_t i : _effectTimeline[frame]) {
        const IFragmentShader* e = _effects[i].get();
        result.push_back({std::string(e->shaderName()), e->paramsAtFrame(frame)});
    }
    return result;
}

Metadata AInput::getMetadata(size_t index)
{
    Metadata meta = index >= _metas.size()
                        ? _metas.back()
                        : _metas[index];

    meta.frameIndex = index;
    meta.argsStatic = !_hasArgsShader;

    return meta;
}
