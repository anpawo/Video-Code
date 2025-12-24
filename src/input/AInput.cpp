/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Input
*/

#include "input/AInput.hpp"

#include <opencv2/core/hal/interface.h>

#include <algorithm>
#include <cstddef>
#include <iostream>
#include <opencv2/core.hpp>
#include <opencv2/core/mat.hpp>

#include "input/IInput.hpp"
#include "input/Metadata.hpp"
#include "transformation/EffectFactory.hpp"
#include "transformation/ITransform.hpp"
#include "utils/Vector.hpp"

AInput::AInput(json::object_t&& args)
    : _baseArgs(std::move(args))
{
}

void AInput::add(json& modification)
{
    std::string name = modification["transformation"];
    json::object_t args = modification["args"];
    size_t start = modification["args"]["start"];
    size_t duration = modification["args"]["duration"];
    std::string type = modification["type"];

    if (type == "transformation") {
        Transform t = getTransformFromString.at(name);

        ///< Find the index
        auto it = std::lower_bound(
            _transformations.begin(),
            _transformations.end(),
            start,
            [](const std::pair<int, std::map<Transform, json::object_t>>& p, int index) {
                return p.first < index;
            }
        );

        ///< If found, override the same transformation (except for args)
        if (it != _transformations.end()) {
            if (t == Transform::Args) {
                for (const auto& i : args) {
                    it->second[t][i.first] = i.second;
                }
            } else {
                it->second[t] = args;
            }
        }
        ///< Else, insert at index
        else {
            if (t == Transform::Args) {
                json::object_t mergedArgs;
                auto prev = it;

                while (prev != _transformations.begin()) {
                    --prev;
                    auto found = prev->second.find(Transform::Args);
                    if (found != prev->second.end()) {
                        mergedArgs = found->second;
                        break;
                    }
                }

                for (const auto& [k, v] : args) {
                    mergedArgs[k] = v;
                }

                _transformations.insert(it, {start, {{Transform::Args, std::move(mergedArgs)}}});
            } else {
                _transformations.insert(it, {start, {{t, args}}});
            }
        }

    } else if (type == "effect") {
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

Metadata AInput::getMetadata(int index)
{
    Metadata meta{.args = _baseArgs};

    if (_transformations.empty()) {
        return meta;
    }

    auto it = std::lower_bound(
        _transformations.begin(),
        _transformations.end(),
        index,
        [](const std::pair<int, std::map<Transform, json::object_t>>& p, int index) {
            return p.first < index;
        }
    );

    // Index > Last Tsf
    if (it == _transformations.end()) {
        it--;
    }

    for (size_t i = 0; i != Transform::__End; i++) {
        Transform t = static_cast<Transform>(i);

        for (auto cp = it;; cp--) {
            auto v = cp->second.find(t);

            if (v != cp->second.end()) {
                getMetadataFromArgs(t, v->second, meta);
                break;
            }
            if (cp == _transformations.begin()) {
                break;
            }
        }
    }

    return meta;
}

/// TODO: use isContinuous() if it is (opti de fou)
void AInput::overlay(cv::Mat& bg, size_t index)
{
    auto meta = getMetadata(index);

    if (meta.hidden) {
        return;
    }

    auto imgMat = getBaseMatrix(meta.args);

    ///< TODO: render needs to keep track of the start index
    if (index < _effectTimeline.size()) {
        const auto& vec = _effectTimeline[index];
        auto end = vec.end();
        std::cout << vec << std::endl;
        for (auto it = vec.begin(); it != end; it++) {
            _effects[*it]->render(imgMat, index);
        }
    }

    auto tsfMat = getTransformationMatrixFromMetadata(imgMat.size(), meta).inv();

    // draw
    for (int y = 0; y < bg.rows; ++y) {
        auto* dstRow = bg.ptr<cv::Vec4b>(y);
        for (int x = 0; x < bg.cols; ++x) {

            cv::Vec3f dstPixel(x, y, 1.0f);
            cv::Vec3f srcPixel = tsfMat * dstPixel;

            float u = srcPixel[0];
            float v = srcPixel[1];

            if (u >= 0 && v >= 0 && u < imgMat.cols && v < imgMat.rows) {
                cv::Vec4b src = imgMat.at<cv::Vec4b>((int)v, (int)u);
                cv::Vec4b& dst = dstRow[x];

                // source alpha
                float alpha = src[3] / 255.0f;

                // B, G, R
                for (int c = 0; c < 3; ++c) {
                    dst[c] = static_cast<uchar>(
                        src[c] * alpha + dst[c] * (1.0f - alpha)
                    );
                }

                // Optional: update destination alpha
                dst[3] = static_cast<uchar>(
                    src[3] + dst[3] * (1.0f - alpha)
                );
            }
        }
    }
}
