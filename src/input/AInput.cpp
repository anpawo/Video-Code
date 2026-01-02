/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Input
*/

#include "input/AInput.hpp"

#include <opencv2/core/hal/interface.h>

#include <cstddef>
#include <opencv2/core.hpp>
#include <opencv2/core/mat.hpp>

#include "effect/ITransform.hpp"
#include "effect/ShaderFactory.hpp"
#include "input/IInput.hpp"
#include "input/Metadata.hpp"

AInput::AInput(json::object_t&& args)
    : _baseArgs(std::move(args))
{
}

void AInput::add(json& modification)
{
    std::string name = modification["name"];
    json::object_t args = modification["args"];
    size_t start = modification["args"]["start"];
    size_t duration = modification["args"]["duration"];
    std::string type = modification["type"];

    if (type == "transformation") {
        Transform t = getTransformFromString.at(name);

        if (start >= _metas.size()) {
            Metadata meta = _metas.back();
            _metas.resize(start + 1, meta);
        }

        getMetadataFromArgs(t, args, _metas[start]);

    } else if (type == "shader") {
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

Metadata AInput::getMetadata(size_t index)
{
    Metadata meta = index >= _metas.size()
                        ? _metas.back()
                        : _metas[index];

    meta.args["index"] = index;

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

        for (auto it = vec.begin(); it != vec.end(); it++) {
            const auto& e = _effects[*it];
            e->render(imgMat, index - e->start());
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
                dst[3] = src[3];
            }
        }
    }
}
