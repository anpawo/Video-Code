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
#include <optional>
#include <vector>

#include "core/Config.hpp"
#include "input/Metadata.hpp"
#include "shader/IVertexShader.hpp"
#include "utils/Color.hpp"
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
        float scale = std::min(1.f / cosHalf, MITER_LIMIT);

        return bisDir * scale;
    }

    // SVG/CSS default miter limit (stepToCorner's clamp).
    static constexpr float MITER_LIMIT = 4.f;

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
            {color[0] / 255.f, color[1] / 255.f, color[2] / 255.f, color[3] / 255.f},
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

        uint32_t base = vertexCount();
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
        addQuadraticStrokePathImpl(localCurves, localStrokeWidth, color, nullptr, std::nullopt, closed, insideOnly);
    }

    // Gradient variant — `gradientDir` is a unit vector in *local* mesh space (same
    // convention as the fill gradient, so it rotates with the shape). Each stroke
    // sample is colored via `lerpGradient(stops, t)` based on its projection onto
    // that direction, normalized across the path's own extent along it — generalizes
    // to any number of color breakpoints, not just a 2-color lerp.
    void addQuadraticStrokePath(
        const std::vector<QuadraticBezier2D> &localCurves,
        float                                 localStrokeWidth,
        const std::vector<GradientStop>      &stops,
        const cv::Vec2f                      &gradientDir,
        bool                                  closed,
        bool                                  insideOnly = false
    )
    {
        addQuadraticStrokePathImpl(localCurves, localStrokeWidth, stops.front().color, &stops, gradientDir, closed, insideOnly);
    }

private:

    void addQuadraticStrokePathImpl(
        const std::vector<QuadraticBezier2D> &localCurves,
        float                                 localStrokeWidth,
        const cv::Vec4b                      &color,
        const std::vector<GradientStop>      *stops,
        std::optional<cv::Vec2f>              gradientDir,
        bool                                  closed,
        bool                                  insideOnly
    )
    {
        if (localCurves.empty()) {
            return;
        }

        // Track local- and world-space points in lockstep so the gradient can be
        // projected in local space (rotates with the shape, matches fill gradient)
        // while stroke geometry is still extruded in world space (matches M scale).
        std::vector<cv::Vec2f> localSamples;
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
                localSamples.push_back(localPoint);
                samples.push_back(toWorldPoint(localPoint[0], localPoint[1]));
            }
        }

        // Remove consecutive near-duplicate samples (produced by degenerate bezier
        // segments) — apply the same removals to localSamples to keep them aligned.
        size_t writeIdx = 0;
        for (size_t readIdx = 0; readIdx < samples.size(); ++readIdx) {
            if (writeIdx == 0 || length2d(samples[readIdx] - samples[writeIdx - 1]) >= 1e-4f) {
                samples[writeIdx] = samples[readIdx];
                localSamples[writeIdx] = localSamples[readIdx];
                ++writeIdx;
            }
        }
        samples.resize(writeIdx);
        localSamples.resize(writeIdx);

        if (samples.size() < 2) {
            return;
        }
        if (closed && length2d(samples.front() - samples.back()) < 1e-4f) {
            samples.pop_back();
            localSamples.pop_back();
        }
        if (samples.size() < 2) {
            return;
        }

        float halfW = std::hypot(M(0, 0), M(1, 0)) * localStrokeWidth * 0.5f;

        // Merge adjacent corner samples that sit closer together than the
        // stroke half-width. Two corners inside one stroke width make their
        // inner offsets cross, folding the strip into a visible notch (e.g.
        // the 'B' bowl junction: font data has two ~70° corners 8 font-units
        // apart). Merged, they form one sharp corner that the bevel join
        // below covers cleanly. Smooth-curve samples turn only a few degrees
        // per sample and are never touched.
        std::vector<bool> mergedCorner(samples.size(), false);
        if (samples.size() >= 4) {
            constexpr float   CORNER_COS = 0.94f; // ~20° — anything sharper is a corner
            size_t            n = samples.size();
            std::vector<bool> isCorner(n, false);
            for (size_t idx = 0; idx < n; ++idx) {
                if (!closed && (idx == 0 || idx + 1 >= n))
                    continue; // open endpoints have no turn
                cv::Vec2f in = normalizeOrZero(samples[idx] - samples[(idx + n - 1) % n]);
                cv::Vec2f out = normalizeOrZero(samples[(idx + 1) % n] - samples[idx]);
                isCorner[idx] = dot2d(in, out) < CORNER_COS;
            }

            size_t w = 0;
            size_t lastOrig = 0; // original index of samples[w-1]
            for (size_t rd = 0; rd < n; ++rd) {
                if (w > 0 && length2d(samples[rd] - samples[w - 1]) < halfW * 0.75f &&
                    isCorner[lastOrig] && isCorner[rd] && !mergedCorner[w - 1]) {
                    samples[w - 1] = (samples[w - 1] + samples[rd]) * 0.5f;
                    localSamples[w - 1] = (localSamples[w - 1] + localSamples[rd]) * 0.5f;
                    mergedCorner[w - 1] = true;
                    continue;
                }
                samples[w] = samples[rd];
                localSamples[w] = localSamples[rd];
                mergedCorner[w] = false;
                lastOrig = rd;
                ++w;
            }
            samples.resize(w);
            localSamples.resize(w);
            mergedCorner.resize(w);

            if (samples.size() < 2)
                return;
        }

        // Expand geometry slightly so fragment shader pixels exist in the fade zone.
        // Actual fade width is computed per-pixel via fwidth() in the shader.
        constexpr float expand = 1.0f;
        float           halfW_expanded = halfW + expand;

        float r = color[0] / 255.f;
        float g = color[1] / 255.f;
        float b = color[2] / 255.f;
        float a = color[3] / 255.f;

        // Precompute per-sample gradient colors (projected in local space, normalized
        // across this path's own extent along the gradient axis).
        std::vector<cv::Vec4f> sampleColors;
        if (gradientDir && stops) {
            const cv::Vec2f &dir = *gradientDir;
            float            minProj = std::numeric_limits<float>::max();
            float            maxProj = std::numeric_limits<float>::lowest();
            for (const auto &p : localSamples) {
                float proj = p[0] * dir[0] + p[1] * dir[1];
                minProj = std::min(minProj, proj);
                maxProj = std::max(maxProj, proj);
            }
            float range = maxProj - minProj;

            sampleColors.reserve(localSamples.size());
            for (const auto &p : localSamples) {
                float     proj = p[0] * dir[0] + p[1] * dir[1];
                float     t = (range > 0.f) ? (proj - minProj) / range : 0.f;
                cv::Vec4b c = lerpGradient(*stops, t);
                sampleColors.push_back({c[0] / 255.f, c[1] / 255.f, c[2] / 255.f, c[3] / 255.f});
            }
        }

        std::vector<uint32_t> pairBases;
        pairBases.reserve(samples.size());

        // World-space data per emitted pair — used after the loop to detect
        // twisted strip quads (offset edges crossing at tight corners) and to
        // patch them with round-join discs.
        struct PairInfo
        {
            cv::Vec2f point, neg, pos;
            cv::Vec4f color;
        };

        std::vector<PairInfo> pairInfos;
        pairInfos.reserve(samples.size());

        // Merged-corner join positions — discs are stamped after the strip,
        // at the corner and at every sample within one stroke radius of it,
        // so their union forms a smooth capsule along the centerline (the
        // exact offset boundary near the joint, hiding the strip's folds).
        std::vector<cv::Vec2f> joinCenters;

        // Full disc of the stroke radius (SVG stroke-linejoin: round): center
        // vertex solid, rim on the stroke boundary so AA matches the strip.
        auto emitJoinDisc = [&](const cv::Vec2f &centerW, const cv::Vec4f &c) {
            constexpr int JOIN_SEGS = 20;
            if (mesh.vertices.size() + JOIN_SEGS + 2 > 250000)
                return; // uint16 index budget — degrade gracefully

            cv::Vec2f centerNdc = toNdcPoint(centerW);
            uint32_t  center = vertexCount();
            mesh.vertices.push_back(Vertex{{centerNdc[0], centerNdc[1]}, {0.f, halfW}, {c[0], c[1], c[2], c[3]}, {2.f, 0.f, 0.f, 0.f}});

            uint32_t prevRim = 0;
            for (int k = 0; k <= JOIN_SEGS; ++k) {
                float     ang = 2.f * static_cast<float>(M_PI) * static_cast<float>(k) / static_cast<float>(JOIN_SEGS);
                cv::Vec2f rimNdc = toNdcPoint(centerW + cv::Vec2f{std::cos(ang), std::sin(ang)} * halfW_expanded);
                uint32_t  rim = vertexCount();
                mesh.vertices.push_back(Vertex{{rimNdc[0], rimNdc[1]}, {halfW_expanded, halfW}, {c[0], c[1], c[2], c[3]}, {2.f, 0.f, 0.f, 0.f}});
                if (k > 0) {
                    mesh.indices.push_back(center);
                    mesh.indices.push_back(prevRim);
                    mesh.indices.push_back(rim);
                }
                prevRim = rim;
            }
        };

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

            float vr = r, vg = g, vb = b, va = a;
            if (gradientDir) {
                const cv::Vec4f &c = sampleColors[i];
                vr = c[0];
                vg = c[1];
                vb = c[2];
                va = c[3];
            }

            auto emitPair = [&](const cv::Vec2f &step) {
                uint32_t base = vertexCount();
                pairBases.push_back(base);

                if (insideOnly) {
                    // Inside stroke: solid strip from the shape boundary inward by strokeWidth.
                    // Outer vertex uv.x = halfW so the fragment shader places it at the clip
                    // threshold, giving AA at the polygon boundary edge. Inner vertex uv.x = 0
                    // (fully inside the stroke, covered by the fill — no fade needed there).
                    cv::Vec2f outerW = point;
                    cv::Vec2f innerW = point + step * 2.f * halfW;
                    cv::Vec2f outerNdc = toNdcPoint(outerW);
                    cv::Vec2f innerNdc = toNdcPoint(innerW);
                    mesh.vertices.push_back(Vertex{{outerNdc[0], outerNdc[1]}, {halfW, halfW}, {vr, vg, vb, va}, {2.f, 0.f, 0.f, 0.f}});
                    mesh.vertices.push_back(Vertex{{innerNdc[0], innerNdc[1]}, {0.f, halfW}, {vr, vg, vb, va}, {2.f, 0.f, 0.f, 0.f}});
                    pairInfos.push_back({point, outerW, innerW, {vr, vg, vb, va}});
                } else {
                    // Centered stroke: ±halfW_expanded around the path centerline
                    cv::Vec2f negW = point - step * halfW_expanded;
                    cv::Vec2f posW = point + step * halfW_expanded;
                    cv::Vec2f negNdc = toNdcPoint(negW);
                    cv::Vec2f posNdc = toNdcPoint(posW);
                    mesh.vertices.push_back(Vertex{{negNdc[0], negNdc[1]}, {-halfW_expanded, halfW}, {vr, vg, vb, va}, {2.f, 0.f, 0.f, 0.f}});
                    mesh.vertices.push_back(Vertex{{posNdc[0], posNdc[1]}, {halfW_expanded, halfW}, {vr, vg, vb, va}, {2.f, 0.f, 0.f, 0.f}});
                    pairInfos.push_back({point, negW, posW, {vr, vg, vb, va}});
                }
            };

            if (!isEndpoint && i < mergedCorner.size() && mergedCorner[i]) {
                // Round join — only at merged corners (two font corners that
                // sat closer than the stroke width): one pair per adjoining
                // segment, each offset exactly perpendicular to its own
                // segment, plus a disc so the two stroke ends flow together
                // with a rounded tip. Ordinary corners keep the classic
                // miter, so triangles/arrows render exactly as before.
                emitPair(leftNormal(prevDir));
                emitPair(leftNormal(nextDir));

                if (!insideOnly) {
                    // Centered strokes: round-join disc at the band midline,
                    // stamped after the strip (with its capsule neighbours).
                    joinCenters.push_back((pairInfos.back().neg + pairInfos.back().pos) * 0.5f);
                }
            } else {
                emitPair(stepToCorner(prevDir, nextDir, isEndpoint));
            }
        }

        if (pairBases.size() < 2) {
            return;
        }

        for (const auto &jc : joinCenters) {
            emitJoinDisc(jc, pairInfos.empty() ? cv::Vec4f{r, g, b, a} : pairInfos.front().color);
            for (const auto &pi : pairInfos) {
                cv::Vec2f mid = (pi.neg + pi.pos) * 0.5f;
                if (length2d(mid - jc) < halfW_expanded && length2d(mid - jc) > 1e-3f)
                    emitJoinDisc(mid, pi.color);
            }
        }

        size_t stripCount = closed ? pairBases.size() : pairBases.size() - 1;
        for (size_t i = 0; i < stripCount; ++i) {
            size_t   j = (i + 1) % pairBases.size();
            uint32_t base0 = pairBases[i];
            uint32_t base1 = pairBases[j];
            mesh.indices.push_back(base0);
            mesh.indices.push_back(base0 + 1);
            mesh.indices.push_back(base1);
            mesh.indices.push_back(base0 + 1);
            mesh.indices.push_back(base1 + 1);
            mesh.indices.push_back(base1);

            // Twisted quad: at corners tighter than the stroke width the two
            // offset edges cross (or reverse), leaving uncovered slivers —
            // visible notches through stroked glyph joints. Patch both ends
            // with round-join discs; they cover everything the bowtie misses.
            {
                const PairInfo &p0 = pairInfos[i];
                const PairInfo &p1 = pairInfos[j];

                auto orient = [](const cv::Vec2f &p, const cv::Vec2f &q, const cv::Vec2f &r) {
                    return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0]);
                };
                auto edgesCross = [&](const cv::Vec2f &a, const cv::Vec2f &b,
                                      const cv::Vec2f &c, const cv::Vec2f &d) {
                    float o1 = orient(a, b, c), o2 = orient(a, b, d);
                    float o3 = orient(c, d, a), o4 = orient(c, d, b);
                    return ((o1 > 0.f) != (o2 > 0.f)) && ((o3 > 0.f) != (o4 > 0.f));
                };

                bool reversed = dot2d(p1.pos - p0.pos, p1.neg - p0.neg) < 0.f;
                bool crossed = edgesCross(p0.neg, p1.neg, p0.pos, p1.pos);
                if (reversed || crossed) {
                    emitJoinDisc((p0.neg + p0.pos) * 0.5f, p0.color);
                    emitJoinDisc((p1.neg + p1.pos) * 0.5f, p1.color);
                }
            }
        }
    }

public:

    void addVertex(float localX, float localY, float u, float v, float opacity = 1.f) // textured variant
    {
        cv::Matx31f world = M * cv::Matx31f{localX, localY, 1.f};

        float ndcX = world(0) / windowWidth - 1.f;
        float ndcY = world(1) / windowHeight - 1.f;

        mesh.vertices.push_back(Vertex{
            {ndcX, ndcY},
            {u, v},
            {0.f, 0.f, 0.f, opacity},
            {3.f, 0.f, 0.f, 0.f}, // mode 3 = texture sample
        });
    }

    void addWorldVertex(float worldX, float worldY, const cv::Vec4b &color)
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
        const std::vector<cv::Vec2f> &worldPts,
        float                         amount,
        bool                          closed
    )
    {
        std::vector<cv::Vec2f> result;
        size_t                 n = worldPts.size();
        result.reserve(n);

        auto sampleAt = [&](int idx) -> const cv::Vec2f & {
            return worldPts[(idx % (int)n + (int)n) % (int)n];
        };

        for (size_t i = 0; i < n; ++i) {
            cv::Vec2f point = worldPts[i];
            cv::Vec2f prevDir = normalizeOrZero(point - sampleAt((int)i - 1));
            cv::Vec2f nextDir = normalizeOrZero(sampleAt((int)i + 1) - point);

            if (length2d(prevDir) < 1e-6f) prevDir = nextDir;
            if (length2d(nextDir) < 1e-6f) nextDir = prevDir;
            if (length2d(prevDir) < 1e-6f || length2d(nextDir) < 1e-6f) {
                result.push_back(point);
                continue;
            }

            bool      isEndpoint = !closed && (i == 0 || i + 1 == n);
            cv::Vec2f step = stepToCorner(prevDir, nextDir, isEndpoint);
            result.push_back(point + step * amount);
        }
        return result;
    }

    uint32_t vertexCount() const
    {
        return static_cast<uint32_t>(mesh.vertices.size());
    }

    MeshFactory &addIndex(uint32_t idx)
    {
        mesh.indices.push_back(idx);
        return *this;
    }

    MeshFactory &setIndices(std::vector<uint32_t> indices)
    {
        mesh.indices = std::move(indices);
        return *this;
    }

    Mesh generateMesh()
    {
        return std::move(mesh);
    }
};
