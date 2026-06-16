/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Input
*/

#pragma once

#include <cmath>
#include <cstddef>
#include <map>
#include <nlohmann/json.hpp>
#include <opencv2/core.hpp>
#include <opencv2/core/mat.hpp>
#include <opencv2/core/matx.hpp>
#include <string>

#include "input/Metadata.hpp"
#include "utils/Exception.hpp"

using json = nlohmann::json;

/*

Transformations affect anything non pixel related in an Input

*/

enum class VertexShader {
    Align,
    Position,
    Translate,
    Scale,
    Rotation,
    Opacity,
    Hide,
    Show,
    Args,
    ZIndex,

    // -

    __End
};

const std::map<std::string, VertexShader> getTransformFromString = {
    {"Position", VertexShader::Position},
    {"Translate", VertexShader::Translate},
    {"Scale", VertexShader::Scale},
    {"Align", VertexShader::Align},
    {"Rotation", VertexShader::Rotation},
    {"Opacity", VertexShader::Opacity},
    {"Hide", VertexShader::Hide},
    {"Show", VertexShader::Show},
    {"Args", VertexShader::Args},
    {"ZIndex", VertexShader::ZIndex},
};

inline cv::Matx33f getTransformationMatrixFromMetadata(const cv::Size2f& size, const Metadata& meta)
{
    float x = meta.position.x;
    float y = meta.position.y;

    float px = size.width * meta.align.x;
    float py = size.height * (1.0f - meta.align.y);

    float rad = meta.rotation * M_PI / 180.0f;
    float c = std::cos(rad);
    float s = std::sin(rad);

    float sx = meta.scale.x;
    float sy = meta.scale.y;

    cv::Matx33f T_pos = cv::Matx33f{
        1, 0, x - px,
        0, 1, y - py,
        0, 0, 1
    };
    cv::Matx33f T_pivot = cv::Matx33f{
        1, 0, px,
        0, 1, py,
        0, 0, 1
    };
    cv::Matx33f R = cv::Matx33f(
        c, -s, 0,
        s, c, 0,
        0, 0, 1
    );
    cv::Matx33f S = cv::Matx33f(
        sx, 0, 0,
        0, sy, 0,
        0, 0, 1
    );
    cv::Matx33f T_neg_pivot = cv::Matx33f{
        1, 0, -px,
        0, 1, -py,
        0, 0, 1
    };

    cv::Matx33f M =
        T_pos *
        T_pivot *
        R *
        S *
        T_neg_pivot;

    return M;
}

inline void getMetadataFromArgs(VertexShader t, const json::object_t& args, Metadata& meta)
{
    switch (t) {
        case VertexShader::__End: {
            throw Error("Impossible __End Transform.");
        }
        case VertexShader::Align: {
            meta.align.x = args.at("x");
            meta.align.y = args.at("y");
            break;
        }
        case VertexShader::Position: {
            meta.position.x = config::screenOffset.x + args.at("x").get<float>() * config::worldToPixelRatio;
            meta.position.y = config::screenOffset.y - args.at("y").get<float>() * config::worldToPixelRatio;
            break;
        }
        case VertexShader::Translate: {
            // Relative shift, in world units — unlike Position, no screenOffset
            // (that's an absolute-origin term, meaningless for a delta).
            meta.position.x += args.at("x").get<float>() * config::worldToPixelRatio;
            meta.position.y -= args.at("y").get<float>() * config::worldToPixelRatio;
            break;
        }
        case VertexShader::Scale: {
            meta.scale.x = args.at("x");
            meta.scale.y = args.at("y");
            break;
        }
        case VertexShader::Rotation: {
            meta.rotation = args.at("degree");
            break;
        }
        case VertexShader::Opacity: {
            meta.opacity = args.at("opacity");
            break;
        }
        case VertexShader::Hide: {
            meta.hidden = true;
            break;
        }
        case VertexShader::Show: {
            meta.hidden = false;
            break;
        }
        case VertexShader::Args: {
            std::string name = args.at("name").get<std::string>();

            // "points"/"contourSizes" live in Metadata::pointsPtr/contourSizesPtr, not
            // argsPtr's json::object_t — swap the typed shared_ptr directly, no JSON
            // clone (see parsePointsJson/parseContourSizesJson in Metadata.hpp).
            if (name == "points") {
                meta.pointsPtr = parsePointsJson(args.at("value"));
                break;
            }
            if (name == "contourSizes") {
                meta.contourSizesPtr = parseContourSizesJson(args.at("value"));
                break;
            }

            // Copy-on-write: args is shared between every Metadata that hasn't
            // diverged, so clone it before mutating this frame's version.
            auto mutableArgs = std::make_shared<json::object_t>(meta.args());
            (*mutableArgs)[name] = args.at("value");
            meta.argsPtr = std::move(mutableArgs);
            break;
        }
        case VertexShader::ZIndex: {
            meta.zIndex = args.at("zIndex").get<int>();
            meta.zOrderSeq = args.at("zOrderSeq").get<int>();
            meta.zIndexExplicit = true;
            break;
        }
    }
}
