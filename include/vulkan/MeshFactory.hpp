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
        , windowWidth(config.screenWidth / 2.f)   // NDC divisor = half reference resolution, independent of preview ratio
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
        bool isEndpoint
    )
    {
        cv::Vec2f n2 = leftNormal(nextDir);

        if (isEndpoint) {
            return n2;
        }

        // Bisect the two normals.
        cv::Vec2f bisector = leftNormal(prevDir) + n2;
        float     bisLen   = length2d(bisector);

        if (bisLen < 1e-6f) {
            return n2;  // 180° reversal — strips antiparallel, bevel.
        }

        cv::Vec2f bisDir  = bisector * (1.f / bisLen);
        float     cosHalf = dot2d(bisDir, n2);  // cos of half the turning angle

        if (std::abs(cosHalf) < 1e-4f) {
            return n2;
        }

        // Bevel past Manim's threshold (cos of full angle < -0.8, i.e. angle > 143°).
        float cos_a = dot2d(prevDir, nextDir);
        if (cos_a < -0.8f) {
            return n2;
        }

        return bisDir * (1.f / cosHalf);
    }

    int quadraticStrokeSteps(const QuadraticBezier2D &curve) const
    {
        cv::Vec2f w0 = toWorldPoint(curve.p0[0], curve.p0[1]);
        cv::Vec2f w1 = toWorldPoint(curve.p1[0], curve.p1[1]);
        cv::Vec2f w2 = toWorldPoint(curve.p2[0], curve.p2[1]);
        float area = 0.5f * std::abs(cross2d(w1 - w0, w2 - w0));
        return std::clamp(2 + static_cast<int>(std::round(std::sqrt(area))), 2, 32);
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
            {0.0f, -1.0f},   // sentinel: solid fill, no Bézier test
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
    void addBezierCap(float p0x, float p0y,
                      float p1x, float p1y,
                      float p2x, float p2y,
                      const cv::Vec4b &color)
    {
        auto toNDC = [&](float lx, float ly, float &nx, float &ny) {
            cv::Matx31f w = M * cv::Matx31f{lx, ly, 1.f};
            nx = w(0) / windowWidth  - 1.f;
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
        float localStrokeWidth,
        const cv::Vec4b &color,
        bool closed
    )
    {
        if (localCurves.empty()) {
            return;
        }

        std::vector<cv::Vec2f> samples;
        for (size_t curveIndex = 0; curveIndex < localCurves.size(); ++curveIndex) {
            const auto &curve = localCurves[curveIndex];
            int steps = quadraticStrokeSteps(curve);
            for (int i = 0; i < steps; ++i) {
                if (curveIndex > 0 && i == 0) {
                    continue;
                }
                float t = static_cast<float>(i) / static_cast<float>(steps - 1);
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

        float widthPx = std::hypot(M(0, 0), M(1, 0)) * localStrokeWidth;
        static constexpr float AAW_PX = 1.5f;
        float halfExtentPx   = 0.5f * (widthPx + AAW_PX);
        float halfWidthToAaw = 0.5f * widthPx / AAW_PX;
        float distNeg        = -halfExtentPx / AAW_PX;
        float distPos        =  halfExtentPx / AAW_PX;

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

            bool isEndpoint = !closed && (i == 0 || i + 1 == samples.size());
            cv::Vec2f step = stepToCorner(prevDir, nextDir, isEndpoint);

            cv::Vec2f negNdc = toNdcPoint(point - step * halfExtentPx);
            cv::Vec2f posNdc = toNdcPoint(point + step * halfExtentPx);

            uint16_t base = vertexCount();
            pairBases.push_back(base);
            mesh.vertices.push_back(Vertex{{negNdc[0], negNdc[1]}, {distNeg, halfWidthToAaw}, {r, g, b, a}, {2.f, 0.f, 0.f, 0.f}});
            mesh.vertices.push_back(Vertex{{posNdc[0], posNdc[1]}, {distPos, halfWidthToAaw}, {r, g, b, a}, {2.f, 0.f, 0.f, 0.f}});
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

    // ── Analytic SDF shape (rounded rect or circle) ──────────────────────────
    //
    // Emits a padded bounding-box quad so the fragment shader can evaluate the
    // exact signed distance to the shape boundary.
    //
    // UV = local position relative to shape centre (world units).
    // Push constants carry hw, hh, r, sw so the frag shader can reconstruct
    // the SDF without any tessellation.
    //
    // cx / cy  – centre of the shape in local (shape) coordinates
    // hw / hh  – half extents (world units = local units here)
    // r        – corner radius
    // sw       – stroke half-width (strokeWidth / 2); 0 = fill only
    //
    // Modes: 3 = SDF fill, 4 = SDF stroke.
    void addSdfShape(
        float cx, float cy,
        float hw, float hh,
        float r,
        float sw,
        const cv::Vec4b &fillColor,
        const cv::Vec4b &strokeColor
    )
    {
        struct ShapePC { float hw, hh, r, sw; };
        setPushConstants(ShapePC{hw, hh, r, sw});

        auto emitQuad = [&](float padX, float padY, const cv::Vec4b &col, float mode) {
            float x0 = cx - hw - padX;
            float y0 = cy - hh - padY;
            float x1 = cx + hw + padX;
            float y1 = cy + hh + padY;

            float fcol[4] = {col[0] / 255.f, col[1] / 255.f, col[2] / 255.f, col[3] / 255.f};

            uint16_t base = vertexCount();
            // UV = local position relative to shape centre
            mesh.vertices.push_back(Vertex{{}, {-(hw + padX), -(hh + padY)}, {fcol[0], fcol[1], fcol[2], fcol[3]}, {mode, 0.f, 0.f, 0.f}});
            mesh.vertices.push_back(Vertex{{}, { (hw + padX), -(hh + padY)}, {fcol[0], fcol[1], fcol[2], fcol[3]}, {mode, 0.f, 0.f, 0.f}});
            mesh.vertices.push_back(Vertex{{}, { (hw + padX),  (hh + padY)}, {fcol[0], fcol[1], fcol[2], fcol[3]}, {mode, 0.f, 0.f, 0.f}});
            mesh.vertices.push_back(Vertex{{}, {-(hw + padX),  (hh + padY)}, {fcol[0], fcol[1], fcol[2], fcol[3]}, {mode, 0.f, 0.f, 0.f}});

            // Fill in the NDC positions now that we know the local coords
            auto setNdc = [&](int vi, float lx, float ly) {
                cv::Matx31f world = M * cv::Matx31f{lx, ly, 1.f};
                mesh.vertices[base + vi].pos[0] = world(0) / windowWidth  - 1.f;
                mesh.vertices[base + vi].pos[1] = world(1) / windowHeight - 1.f;
            };
            setNdc(0, x0, y0);
            setNdc(1, x1, y0);
            setNdc(2, x1, y1);
            setNdc(3, x0, y1);

            mesh.indices.push_back(base + 0);
            mesh.indices.push_back(base + 1);
            mesh.indices.push_back(base + 2);
            mesh.indices.push_back(base + 0);
            mesh.indices.push_back(base + 2);
            mesh.indices.push_back(base + 3);
        };

        // aaw = length(dFd*) * 2 ≈ 1 SSAA pixel in world units ≈ 0.5–1 world unit.
        // A 2 world-unit pad is more than enough for the AA fade to complete.
        constexpr float AAW = 2.0f;

        if (fillColor[3] > 0) {
            emitQuad(AAW, AAW, fillColor, 3.f);
        }
        if (strokeColor[3] > 0 && sw > 0.f) {
            emitQuad(sw + AAW, sw + AAW, strokeColor, 4.f);
        }
    }

    void addBezierStroke(float p0x, float p0y,
                         float p1x, float p1y,
                         float p2x, float p2y,
                         float localStrokeWidth, const cv::Vec4b &color)
    {
        addQuadraticStrokePath({
            QuadraticBezier2D{
                {p0x, p0y},
                {p1x, p1y},
                {p2x, p2y},
            }
        }, localStrokeWidth, color, false);
    }

    void addVertex(float localX, float localY, float u, float v) // textured variant
    {
        cv::Matx31f world = M * cv::Matx31f{localX, localY, 1.f};

        float ndcX = world(0) / windowWidth * 2.f - 1.f;
        float ndcY = world(1) / windowHeight * 2.f - 1.f;

        mesh.vertices.push_back(Vertex{
            {ndcX, ndcY},
            {u, v},
            {},
            {0.f, 0.f, 0.f, 0.f},
        });
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

    // MeshBuilder &setTexture(TextureDescriptor *descriptor)
    // {
    //     mesh.hasTexture = true;
    //     mesh.textureDescriptor = descriptor;
    //     return *this;
    // }

    template <typename T>
    MeshFactory &setPushConstants(const T &pc)
    {
        const uint8_t *bytes = reinterpret_cast<const uint8_t *>(&pc);
        mesh.pushConstantData.assign(bytes, bytes + sizeof(T));
        return *this;
    }

    Mesh generateMesh()
    {
        return std::move(mesh);
    }
};
