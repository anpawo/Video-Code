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

enum Transform {
    Align,
    Position,
    Scale,
    Rotate,
    Hide,
    Show,
    Args,

    // -

    __End
};

const std::map<std::string, Transform> getTransformFromString = {
    {"Position", Transform::Position},
    {"Scale", Transform::Scale},
    {"Align", Transform::Align},
    {"Rotate", Transform::Rotate},
    {"Hide", Transform::Hide},
    {"Show", Transform::Show},
    {"Args", Transform::Args},
};

inline cv::Matx33f getTransformationMatrixFromMetadata(const cv::Size& size, const Metadata& meta)
{
    float x = meta.position.x;
    float y = meta.position.y;

    float px = size.width * meta.align.x;
    float py = size.height * meta.align.y;

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

inline void getMetadataFromArgs(Transform t, const json::object_t& args, Metadata& meta)
{
    switch (t) {
        case __End: {
            throw Error("Impossible __End Transform.");
        }
        case Align: {
            meta.align.x = args.at("x");
            meta.align.y = args.at("y");
            break;
        }
        case Position: {
            meta.position.x = config::screenOffset.x + args.at("x").get<float>();
            meta.position.y = config::screenOffset.y - args.at("y").get<float>();
            break;
        }
        case Scale: {
            meta.scale.x = args.at("x");
            meta.scale.y = args.at("y");
            break;
        }
        case Rotate: {
            meta.rotation = args.at("degree");
            break;
        }
        case Hide: {
            meta.hidden = true;
            break;
        }
        case Show: {
            meta.hidden = false;
            break;
        }
        case Args: {
            meta.args[args.at("name")] = args.at("value");
            break;
        }
    }
}
