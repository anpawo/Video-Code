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

namespace
{
    // Pops "points"/"contourSizes" out of the Create() args (mutating in place) so the
    // canonical json::object_t never carries them — see Metadata::pointsPtr/contourSizesPtr.
    std::shared_ptr<const std::vector<cv::Vec2f>> extractPoints(json::object_t& args)
    {
        auto it = args.find("points");
        if (it == args.end())
            return nullptr;
        auto points = parsePointsJson(it->second);
        args.erase(it);
        return points;
    }

    std::shared_ptr<const std::vector<size_t>> extractContourSizes(json::object_t& args)
    {
        auto it = args.find("contourSizes");
        if (it == args.end())
            return nullptr;
        auto sizes = parseContourSizesJson(it->second);
        args.erase(it);
        return sizes;
    }
}

AInput::AInput(json::object_t&& args)
    : _initialPoints(extractPoints(args))
    , _initialContourSizes(extractContourSizes(args))
    , _baseArgsPtr(std::make_shared<const json::object_t>(std::move(args)))
    , _baseArgs(*_baseArgsPtr)
{
}

void AInput::resetModifications()
{
    _hasArgsShader = false;
    _effects.clear();
    _effectTimeline.clear();
    _metas = {Metadata{
        .argsPtr = _baseArgsPtr,
        .pointsPtr = _initialPoints,
        .contourSizesPtr = _initialContourSizes,
    }};
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

std::vector<ActiveEffect> AInput::getActiveEffectsAtFrame(size_t frame, const ClockStops& stops) const
{
    std::vector<ActiveEffect> result;

    // Shader fill (fillColor = a PaintShader on the Python side): fills are
    // per-frame STATE, not timeline effects — the {"shader": ...} object
    // rides args["fillColor"] exactly like a color and persists until
    // reassigned, so it is injected here on every frame it is active.
    // Injected FIRST: timeline effects (.apply()) post-process the fill.
    {
        const Metadata& meta = _metas[std::min(frame, _metas.size() - 1)];
        const auto&     margs = meta.args();
        auto            fill = margs.find("fillColor");
        if (fill != margs.end() && fill->second.is_object() && fill->second.contains("shader")) {
            ActiveEffect fe{fill->second.at("shader").get<std::string>(), {}, false, -1};
            // Numeric args in ALPHABETICAL order (json::object_t sorts keys)
            // — the same p[] contract every effect follows — then the paint's
            // clock: frames elapsed since this fill was assigned.
            for (const auto& [k, v] : fill->second.items()) {
                if (v.is_number())
                    fe.params.push_back(v.get<float>());
                else if (k == "filepath" && v.is_string())
                    fe.strParam = v.get<std::string>();
            }
            // The paint clock counts from the fill's assignment, minus any
            // frames a wait(stop=Clock.PAINTS)/freeze() held it.
            size_t since = std::min(frame, meta.fillShaderSince);
            size_t elapsed = (frame - since) - ClockStops::pausedBetween(stops.paints, since, frame);
            fe.params.push_back(static_cast<float>(elapsed));
            result.push_back(std::move(fe));
        }
    }

    if (frame >= _effectTimeline.size())
        return result;

    for (size_t i : _effectTimeline[frame]) {
        const IFragmentShader* e = _effects[i].get();
        // Activation is scheduling (real frame); PROGRESS is an ambient clock
        // — subtract frames a wait(stop=Clock.EFFECTS)/freeze() held it since
        // this effect started.
        size_t effectFrame = frame - ClockStops::pausedBetween(stops.effects, e->start(), frame);
        ActiveEffect ae{std::string(e->shaderName()), e->paramsAtFrame(effectFrame), e->needsBBox(), e->groupParamIndex()};

        // Carry a file-path string arg straight through (not via the numeric
        // p[] path — a string can't be a push-constant float). `lut` uses this
        // as the .cube cache key in the renderers; other effects have no
        // "filepath" arg so this stays empty.
        const auto& a = e->args();
        auto        it = a.find("filepath");
        if (it != a.end() && it->second.is_string())
            ae.strParam = it->second.get<std::string>();

        result.push_back(std::move(ae));
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
