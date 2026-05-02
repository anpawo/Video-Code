/*
** EPITECH PROJECT, 2026
** video-code
** File description:
** Vertex
*/

#pragma once

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <opencv2/core/matx.hpp>
#include <opencv2/core/types.hpp>
#include <vector>

#include "core/Config.hpp"
#include "input/Metadata.hpp"
#include "shader/IVertexShader.hpp"
#include "vulkan/Mesh.hpp"

struct QuadraticBezier2D
{
    cv::Vec2f p0;
    cv::Vec2f p1;
    cv::Vec2f p2;
};

struct MeshFactory
{
    Mesh mesh;

    cv::Matx33f M;
    cv::Size2f  localSize;

    float windowWidth;
    float windowHeight;

    // ---

    MeshFactory(const cv::Size2f &localSize, const Metadata &meta, const Config &config)
        : M(getTransformationMatrixFromMetadata(localSize, meta))
        , localSize(localSize)
        , windowWidth(config.screenWidth / 2.f) // NDC divisor = half reference resolution, independent of preview ratio
        , windowHeight(config.screenHeight / 2.f)
    {
    }

    cv::Vec2f toWorldPoint(float localX, float localY) const
    {
        cv::Matx31f world = M * cv::Matx31f{localX, localY, 1.f};
        return {world(0), world(1)};
    }

    cv::Vec2f toNdcPoint(const cv::Vec2f &world) const
    {
        return {
            world[0] / windowWidth - 1.f,
            world[1] / windowHeight - 1.f,
        };
    }

    static cv::Vec2f evalQuadratic(const QuadraticBezier2D &curve, float t)
    {
        float u = 1.f - t;
        return u * u * curve.p0 + 2.f * u * t * curve.p1 + t * t * curve.p2;
    }

    static float cross2d(const cv::Vec2f &a, const cv::Vec2f &b)
    {
        return a[0] * b[1] - a[1] * b[0];
    }

    static float dot2d(const cv::Vec2f &a, const cv::Vec2f &b)
    {
        return a[0] * b[0] + a[1] * b[1];
    }

    static float length2d(const cv::Vec2f &v)
    {
        return std::hypot(v[0], v[1]);
    }

    static cv::Vec2f normalizeOrZero(const cv::Vec2f &v)
    {
        float len = length2d(v);
        if (len < 1e-6f) {
            return {0.f, 0.f};
        }
        return v * (1.f / len);
    }

    static cv::Vec2f leftNormal(const cv::Vec2f &v)
    {
        return {-v[1], v[0]};
    }

    // Classic miter step for a flat (2D) polyline.
    // prevDir and nextDir must be unit vectors.
    // isEndpoint = true when one side has no neighbour (open path start/end).
    //
    // Returns the perpendicular offset step vector — NOT unit-length.
    // Multiply by halfExtentPx to get the world-space corner offset.
    //
    // For smooth-curve interior points (tiny turn angle) scale ≈ 1.0 — the
    // tiny correction fills the inter-quad gap and makes the strip tile exactly.
    // For moderate corners scale = 1/cos(θ/2) — the classic miter intersection.
    // For angles > 143° (Manim's MITER_COS_ANGLE_THRESHOLD = -0.8) we bevel:
    // return the simple perpendicular and let the two strips leave a small gap
    // that the AA region covers — same as Manim's bevel fallback.
    static cv::Vec2f stepToCorner(
        const cv::Vec2f &prevDir,
        const cv::Vec2f &nextDir,
        bool             isEndpoint
    )
    {
        cv::Vec2f n2 = leftNormal(nextDir);

        if (isEndpoint) {
            return n2;
        }

        // Bisect the two normals.
        cv::Vec2f bisector = leftNormal(prevDir) + n2;
        float     bisLen = length2d(bisector);

        if (bisLen < 1e-6f) {
            return n2; // 180° reversal — strips antiparallel, bevel.
        }

        cv::Vec2f bisDir = bisector * (1.f / bisLen);
        float     cosHalf = dot2d(bisDir, n2); // cos of half the turning angle

        if (std::abs(cosHalf) < 1e-4f) {
            return n2;
        }

        // Cap the miter so spikes at sharp corners never exceed MITER_LIMIT × halfStrokeWidth.
        // Matches the SVG/CSS default miter-limit of 4: angles with interior < ~29° get a
        // small bevel at the tip; everything else is a proper miter join.
        constexpr float MITER_LIMIT = 4.f;
        float scale = std::min(1.f / cosHalf, MITER_LIMIT);

        return bisDir * scale;
    }

    int quadraticStrokeSteps(const QuadraticBezier2D &curve) const
    {
        cv::Vec2f w0 = toWorldPoint(curve.p0[0], curve.p0[1]);
        cv::Vec2f w1 = toWorldPoint(curve.p1[0], curve.p1[1]);
        cv::Vec2f w2 = toWorldPoint(curve.p2[0], curve.p2[1]);
        float     area = 0.5f * std::abs(cross2d(w1 - w0, w2 - w0));
        float     chordLen = length2d(w2 - w0);
        float     flatness = chordLen > 1e-6f ? std::abs(cross2d(w1 - w0, w2 - w0)) / chordLen : 0.f;
        int       steps = 2 + static_cast<int>(std::round(std::sqrt(area) + flatness * 0.5f));
        return std::clamp(steps, 2, 64);
    }

    // Shape calls this for each local-space corner.
    // UV is set to the sentinel (0, -1) so the fragment shader skips the
    // Bézier curve test and outputs solid color.
    void addVertex(float localX, float localY, const cv::Vec4b &color)
    {
        cv::Matx31f world = M * cv::Matx31f{localX, localY, 1.f};

        float ndcX = world(0) / windowWidth - 1.f;
        float ndcY = world(1) / windowHeight - 1.f;

        mesh.vertices.push_back(Vertex{
            {ndcX, ndcY},
            {0.0f, -1.0f}, // sentinel: solid fill, no Bézier test
            {color[0] / 255.f,
             color[1] / 255.f,
             color[2] / 255.f,
             color[3] / 255.f
            },
            {0.f, 0.f, 0.f, 0.f},
        });
    }

    // Emits a Bézier cap triangle for a convex quadratic arc (p0 → p1 → p2).
    // p1 is the tangent-intersection control point (outside the filled region).
    // Uses Loop-Blinn UV coordinates:
    //   p0 → (0, 0),  p1 → (0.5, 0),  p2 → (1, 1)
    // In the fragment shader the curve is the zero-set of K = u² - v.
    // Pixels with K > 0 (on the p1 side) are discarded with smooth AA.
    void addBezierCap(float p0x, float p0y, float p1x, float p1y, float p2x, float p2y, const cv::Vec4b &color)
    {
        auto toNDC = [&](float lx, float ly, float &nx, float &ny) {
            cv::Matx31f w = M * cv::Matx31f{lx, ly, 1.f};
            nx = w(0) / windowWidth - 1.f;
            ny = w(1) / windowHeight - 1.f;
        };

        float nx0, ny0, nx1, ny1, nx2, ny2;
        toNDC(p0x, p0y, nx0, ny0);
        toNDC(p1x, p1y, nx1, ny1);
        toNDC(p2x, p2y, nx2, ny2);

        float r = color[0] / 255.f, g = color[1] / 255.f;
        float b = color[2] / 255.f, a = color[3] / 255.f;

        uint16_t base = vertexCount();
        mesh.vertices.push_back(Vertex{{nx0, ny0}, {0.0f, 0.0f}, {r, g, b, a}, {1.f, 0.f, 0.f, 0.f}});
        mesh.vertices.push_back(Vertex{{nx1, ny1}, {0.5f, 0.0f}, {r, g, b, a}, {1.f, 0.f, 0.f, 0.f}});
        mesh.vertices.push_back(Vertex{{nx2, ny2}, {1.0f, 1.0f}, {r, g, b, a}, {1.f, 0.f, 0.f, 0.f}});
        mesh.indices.push_back(base);
        mesh.indices.push_back(base + 1);
        mesh.indices.push_back(base + 2);
    }

    void addQuadraticStrokePath(
        const std::vector<QuadraticBezier2D> &localCurves,
        float                                 localStrokeWidth,
        const cv::Vec4b                      &color,
        bool                                  closed,
        bool                                  insideOnly = false
    )
    {
        if (localCurves.empty()) {
            return;
        }

        std::vector<cv::Vec2f> samples;
        for (size_t curveIndex = 0; curveIndex < localCurves.size(); ++curveIndex) {
            const auto &curve = localCurves[curveIndex];
            int         steps = quadraticStrokeSteps(curve);
            for (int i = 0; i < steps; ++i) {
                if (curveIndex > 0 && i == 0) {
                    continue;
                }
                float     t = static_cast<float>(i) / static_cast<float>(steps - 1);
                cv::Vec2f localPoint = evalQuadratic(curve, t);
                samples.push_back(toWorldPoint(localPoint[0], localPoint[1]));
            }
        }

        if (samples.size() < 2) {
            return;
        }
        if (closed && length2d(samples.front() - samples.back()) < 1e-4f) {
            samples.pop_back();
        }
        if (samples.size() < 2) {
            return;
        }

        float halfW = std::hypot(M(0, 0), M(1, 0)) * localStrokeWidth * 0.5f;

        // Expand geometry slightly so fragment shader pixels exist in the fade zone.
        // Actual fade width is computed per-pixel via fwidth() in the shader.
        constexpr float expand = 1.0f;
        float           halfW_expanded = halfW + expand;

        float r = color[0] / 255.f;
        float g = color[1] / 255.f;
        float b = color[2] / 255.f;
        float a = color[3] / 255.f;

        std::vector<uint16_t> pairBases;
        pairBases.reserve(samples.size());

        auto sampleAt = [&](int index) -> const cv::Vec2f & {
            int n = static_cast<int>(samples.size());
            return samples[(index % n + n) % n];
        };

        for (size_t i = 0; i < samples.size(); ++i) {
            cv::Vec2f point = samples[i];
            cv::Vec2f prevDir;
            cv::Vec2f nextDir;

            if (closed || i > 0) {
                prevDir = normalizeOrZero(point - sampleAt(static_cast<int>(i) - 1));
            }
            if (closed || i + 1 < samples.size()) {
                nextDir = normalizeOrZero(sampleAt(static_cast<int>(i) + 1) - point);
            }

            if (length2d(prevDir) < 1e-6f) {
                prevDir = nextDir;
            }
            if (length2d(nextDir) < 1e-6f) {
                nextDir = prevDir;
            }
            if (length2d(prevDir) < 1e-6f || length2d(nextDir) < 1e-6f) {
                continue;
            }

            bool      isEndpoint = !closed && (i == 0 || i + 1 == samples.size());
            cv::Vec2f step = stepToCorner(prevDir, nextDir, isEndpoint);

            uint16_t base = vertexCount();
            pairBases.push_back(base);

            if (insideOnly) {
                // Inside stroke: solid strip from the shape boundary inward by strokeWidth.
                // No inner expand — the fill polygon starts exactly at the inner edge,
                // so no fade is needed there (SSAA handles the outer boundary edge).
                cv::Vec2f outerNdc = toNdcPoint(point);
                cv::Vec2f innerNdc = toNdcPoint(point + step * 2.f * halfW);
                mesh.vertices.push_back(Vertex{{outerNdc[0], outerNdc[1]}, {0.f, halfW}, {r, g, b, a}, {2.f, 0.f, 0.f, 0.f}});
                mesh.vertices.push_back(Vertex{{innerNdc[0], innerNdc[1]}, {0.f, halfW}, {r, g, b, a}, {2.f, 0.f, 0.f, 0.f}});
            } else {
                // Centered stroke: ±halfW_expanded around the path centerline
                cv::Vec2f negNdc = toNdcPoint(point - step * halfW_expanded);
                cv::Vec2f posNdc = toNdcPoint(point + step * halfW_expanded);
                mesh.vertices.push_back(Vertex{{negNdc[0], negNdc[1]}, {-halfW_expanded, halfW}, {r, g, b, a}, {2.f, 0.f, 0.f, 0.f}});
                mesh.vertices.push_back(Vertex{{posNdc[0], posNdc[1]}, {halfW_expanded,  halfW}, {r, g, b, a}, {2.f, 0.f, 0.f, 0.f}});
            }
        }

        if (pairBases.size() < 2) {
            return;
        }

        size_t stripCount = closed ? pairBases.size() : pairBases.size() - 1;
        for (size_t i = 0; i < stripCount; ++i) {
            uint16_t base0 = pairBases[i];
            uint16_t base1 = pairBases[(i + 1) % pairBases.size()];
            mesh.indices.push_back(base0);
            mesh.indices.push_back(base0 + 1);
            mesh.indices.push_back(base1);
            mesh.indices.push_back(base0 + 1);
            mesh.indices.push_back(base1 + 1);
            mesh.indices.push_back(base1);
        }
    }

    void addVertex(float localX, float localY, float u, float v, float opacity = 1.f) // textured variant
    {
        cv::Matx31f world = M * cv::Matx31f{localX, localY, 1.f};

        float ndcX = world(0) / windowWidth - 1.f;
        float ndcY = world(1) / windowHeight - 1.f;

        mesh.vertices.push_back(Vertex{
            {ndcX, ndcY},
            {u, v},
            {0.f, 0.f, 0.f, opacity},
            {3.f, 0.f, 0.f, 0.f},     // mode 3 = texture sample
        });
    }

    void addWorldVertex(float worldX, float worldY, const cv::Vec4b& color)
    {
        float ndcX = worldX / windowWidth - 1.f;
        float ndcY = worldY / windowHeight - 1.f;
        mesh.vertices.push_back(Vertex{
            {ndcX, ndcY},
            {0.0f, -1.0f},
            {color[0] / 255.f, color[1] / 255.f, color[2] / 255.f, color[3] / 255.f},
            {0.f, 0.f, 0.f, 0.f},
        });
    }

    // Inset a closed world-space polyline inward by `amount`.
    // For CW paths (screen y-down), the left-normal points inward.
    static std::vector<cv::Vec2f> insetPolyWorld(
        const std::vector<cv::Vec2f>& worldPts,
        float                         amount,
        bool                          closed
    )
    {
        std::vector<cv::Vec2f> result;
        size_t n = worldPts.size();
        result.reserve(n);

        auto sampleAt = [&](int idx) -> const cv::Vec2f& {
            return worldPts[(idx % (int)n + (int)n) % (int)n];
        };

        for (size_t i = 0; i < n; ++i) {
            cv::Vec2f point   = worldPts[i];
            cv::Vec2f prevDir = normalizeOrZero(point - sampleAt((int)i - 1));
            cv::Vec2f nextDir = normalizeOrZero(sampleAt((int)i + 1) - point);

            if (length2d(prevDir) < 1e-6f) prevDir = nextDir;
            if (length2d(nextDir) < 1e-6f) nextDir = prevDir;
            if (length2d(prevDir) < 1e-6f || length2d(nextDir) < 1e-6f) {
                result.push_back(point);
                continue;
            }

            bool      isEndpoint = !closed && (i == 0 || i + 1 == n);
            cv::Vec2f step       = stepToCorner(prevDir, nextDir, isEndpoint);
            result.push_back(point + step * amount);
        }
        return result;
    }

    uint16_t vertexCount() const
    {
        return static_cast<uint16_t>(mesh.vertices.size());
    }

    MeshFactory &addIndex(uint16_t idx)
    {
        mesh.indices.push_back(idx);
        return *this;
    }

    MeshFactory &setIndices(std::vector<uint16_t> indices)
    {
        mesh.indices = std::move(indices);
        return *this;
    }

    Mesh generateMesh()
    {
        return std::move(mesh);
    }
};
