/*
** EPITECH PROJECT, 2026
** video-code
** File description:
** Vertex
*/

#pragma once

#include <cstdint>
#include <opencv2/core/matx.hpp>
#include <opencv2/core/types.hpp>
#include <vector>

#include "core/Config.hpp"
#include "input/Metadata.hpp"
#include "shader/IVertexShader.hpp"
#include "vulkan/Mesh.hpp"

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
        mesh.vertices.push_back(Vertex{{nx0, ny0}, {0.0f, 0.0f}, {r, g, b, a}});
        mesh.vertices.push_back(Vertex{{nx1, ny1}, {0.5f, 0.0f}, {r, g, b, a}});
        mesh.vertices.push_back(Vertex{{nx2, ny2}, {1.0f, 1.0f}, {r, g, b, a}});
        mesh.indices.push_back(base);
        mesh.indices.push_back(base + 1);
        mesh.indices.push_back(base + 2);
    }

    // Tessellates one quadratic Bezier stroke arc into triangle-strip quads
    // and appends them directly to the regular fill vertex/index buffers.
    //
    // UV encoding used for stroke quads (Manim-style SDF):
    //   uv.x  = distToAaw    — signed perp-distance / AA-width (interpolated)
    //   uv.y  = halfWidthToAaw + 2.0   (always ≥ 2, distinguishes stroke from
    //                                    solid fill (uv.y<0) and Loop-Blinn (uv.y∈[0,1]))
    //
    // The fragment shader reads these and computes:
    //   signedDist = abs(uv.x) - (uv.y - 2.0)
    //   alpha      = smoothstep(0.5, -0.5, signedDist)
    void addBezierStroke(float p0x, float p0y,
                         float p1x, float p1y,
                         float p2x, float p2y,
                         float localStrokeWidth, const cv::Vec4b &color)
    {
        // ── NDC positions ────────────────────────────────────────────────────
        auto toNDC = [&](float lx, float ly, float &nx, float &ny) {
            cv::Matx31f w = M * cv::Matx31f{lx, ly, 1.f};
            nx = w(0) / windowWidth  - 1.f;
            ny = w(1) / windowHeight - 1.f;
        };

        float nx0, ny0, nx1, ny1, nx2, ny2;
        toNDC(p0x, p0y, nx0, ny0);
        toNDC(p1x, p1y, nx1, ny1);
        toNDC(p2x, p2y, nx2, ny2);

        // ── Stroke metrics in screen pixels ─────────────────────────────────
        float widthPx = std::hypot(M(0, 0), M(1, 0)) * localStrokeWidth;

        static constexpr float AAW_PX = 1.5f;
        float halfExtentPx   = 0.5f * (widthPx + AAW_PX);
        float halfWidthToAaw = 0.5f * widthPx / AAW_PX;
        float uvY            = halfWidthToAaw + 2.0f;
        float distNeg        = -halfExtentPx / AAW_PX;
        float distPos        =  halfExtentPx / AAW_PX;

        float r = color[0] / 255.f, g = color[1] / 255.f;
        float b = color[2] / 255.f, a = color[3] / 255.f;

        // ── Adaptive step count ──────────────────────────────────────────────
        float len01 = std::hypot((nx1-nx0)*windowWidth, (ny1-ny0)*windowHeight);
        float len12 = std::hypot((nx2-nx1)*windowWidth, (ny2-ny1)*windowHeight);
        int nSteps  = std::clamp(2 + (int)((len01 + len12) / 4.f), 2, 32);

        // ── Bezier: P(t) = c0 + c1·t + c2·t² ───────────────────────────────
        float c0x = nx0,             c0y = ny0;
        float c1x = 2.f*(nx1-nx0),  c1y = 2.f*(ny1-ny0);
        float c2x = nx0-2.f*nx1+nx2, c2y = ny0-2.f*ny1+ny2;

        auto evalPt = [&](float t) {
            return std::make_pair(c0x + c1x*t + c2x*t*t,
                                  c0y + c1y*t + c2y*t*t);
        };
        auto evalTan = [&](float t) {
            return std::make_pair(c1x + 2.f*c2x*t,
                                  c1y + 2.f*c2y*t);
        };

        // ── Screen-space perpendicular → NDC offset ──────────────────────────
        auto perpOff = [&](float t, float distPx, float &ox, float &oy) {
            auto [tx, ty] = evalTan(t);
            float txPx = tx * windowWidth,  tyPx = ty * windowHeight;
            float len  = std::hypot(txPx, tyPx);
            if (len < 1e-6f) {
                txPx = (nx2-nx0)*windowWidth;
                tyPx = (ny2-ny0)*windowHeight;
                len  = std::hypot(txPx, tyPx);
            }
            float pxPx = -tyPx / len,  pyPx = txPx / len; // unit perp in px
            ox = pxPx * distPx / windowWidth;
            oy = pyPx * distPx / windowHeight;
        };

        // ── Emit one quad per polyline segment ───────────────────────────────
        for (int i = 0; i < nSteps - 1; i++) {
            float t0 = float(i)     / float(nSteps - 1);
            float t1 = float(i + 1) / float(nSteps - 1);

            auto [px0, py0] = evalPt(t0);
            auto [px1, py1] = evalPt(t1);

            float ox0n, oy0n, ox0p, oy0p;
            float ox1n, oy1n, ox1p, oy1p;
            perpOff(t0, -halfExtentPx, ox0n, oy0n);
            perpOff(t0,  halfExtentPx, ox0p, oy0p);
            perpOff(t1, -halfExtentPx, ox1n, oy1n);
            perpOff(t1,  halfExtentPx, ox1p, oy1p);

            uint16_t base = vertexCount();
            mesh.vertices.push_back(Vertex{{px0+ox0n, py0+oy0n}, {distNeg, uvY}, {r, g, b, a}});
            mesh.vertices.push_back(Vertex{{px0+ox0p, py0+oy0p}, {distPos, uvY}, {r, g, b, a}});
            mesh.vertices.push_back(Vertex{{px1+ox1n, py1+oy1n}, {distNeg, uvY}, {r, g, b, a}});
            mesh.vertices.push_back(Vertex{{px1+ox1p, py1+oy1p}, {distPos, uvY}, {r, g, b, a}});

            mesh.indices.push_back(base);
            mesh.indices.push_back(base + 1);
            mesh.indices.push_back(base + 2);
            mesh.indices.push_back(base + 1);
            mesh.indices.push_back(base + 3);
            mesh.indices.push_back(base + 2);
        }
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
