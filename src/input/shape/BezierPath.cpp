/*
** EPITECH PROJECT, 2026
** video-code
** File description:
** BezierPath
*/

#include "input/shape/BezierPath.hpp"

#include <algorithm>
#include <cmath>
#include <mapbox/earcut.hpp>

#include "vulkan/MeshFactory.hpp"
#include "utils/Color.hpp"
#include "utils/Logger.hpp"

#ifdef VC_DEBUG_ON
#  include <chrono>
#  define BP_T(name)  auto name = std::chrono::high_resolution_clock::now()
#  define BP_US(a, b) std::chrono::duration_cast<std::chrono::microseconds>((b) - (a)).count()
#else
#  define BP_T(name)  [[maybe_unused]] int name = 0
#  define BP_US(a, b) 0L
#endif

BezierPath::BezierPath(json::object_t&& args)
    : AInput(std::move(args))
{
}

// FNV-1a 64-bit hash over raw bytes, chainable (pass previous hash as seed).
static size_t fnvHash(const void* data, size_t bytes, size_t h = 0xcbf29ce484222325ULL)
{
    constexpr size_t PRIME = 0x00000100000001B3ULL;
    const auto*      p     = static_cast<const uint8_t*>(data);
    for (size_t i = 0; i < bytes; ++i)
        h = (h ^ p[i]) * PRIME;
    return h;
}

// Sutherland-Hodgman polygon clip against a single half-plane.
// insideIsAbove=true keeps vertices where (p · dir) >= threshold.
// insideIsAbove=false keeps vertices where (p · dir) <= threshold.
// Works correctly for convex inputs; simple (non-self-intersecting) for typical
// non-convex inputs encountered in practice (rectangles, circles, arrows).
static std::vector<cv::Vec2f> clipPolyHalfPlane(
    const std::vector<cv::Vec2f>& poly,
    const cv::Vec2f&              dir,
    float                         threshold,
    bool                          insideIsAbove)
{
    if (poly.empty()) return {};
    std::vector<cv::Vec2f> out;
    out.reserve(poly.size() + 1);
    size_t n = poly.size();
    for (size_t i = 0; i < n; ++i) {
        const cv::Vec2f& a  = poly[i];
        const cv::Vec2f& b  = poly[(i + 1) % n];
        float            pa = a[0] * dir[0] + a[1] * dir[1];
        float            pb = b[0] * dir[0] + b[1] * dir[1];
        bool             ia = insideIsAbove ? (pa >= threshold) : (pa <= threshold);
        bool             ib = insideIsAbove ? (pb >= threshold) : (pb <= threshold);
        if (ia)
            out.push_back(a);
        if (ia != ib) {
            float alpha = (threshold - pa) / (pb - pa);
            out.push_back(a + alpha * (b - a));
        }
    }
    return out;
}

void BezierPath::parseColorOrGradient(
    const json::object_t& args, const std::string& key,
    cv::Vec4b& color, std::vector<GradientStop>& stops, GradType& gradType, float& angle)
{
    const auto& colorJson = args.at(key);

    // LinearGradient / RadialGradient / ConicGradient emit [stops_array, discriminator].
    // Linear:  discriminator is a number (the angle in degrees).
    // Radial:  discriminator is the string "radial".
    // Conic:   discriminator is ["conic", angle_in_degrees].
    // Solid rgba is a flat 4-element number array.
    if (colorJson.is_array() && colorJson.size() == 2 && colorJson[0].is_array()) {
        const auto& stopsJson = colorJson[0];
        stops.clear();
        stops.reserve(stopsJson.size());
        for (const auto& stopJson : stopsJson) {
            stops.push_back(GradientStop{
                colorFromJson(stopJson[0], 255),
                stopJson[1].get<float>() / 100.f,
            });
        }
        if (colorJson[1].is_string()) {
            gradType = GradType::Radial;
        } else if (colorJson[1].is_array()) {
            angle    = colorJson[1][1].get<float>();
            gradType = GradType::Conic;
        } else {
            angle    = colorJson[1].get<float>();
            gradType = GradType::Linear;
        }
    } else {
        color    = colorFromJson(colorJson, 255);
        gradType = GradType::None;
    }
}

Mesh BezierPath::getMesh(const Metadata& meta, const Config& config)
{
    BP_T(t0);

    // --- Fast path: skip buildPath entirely when args are known static ----------
    // meta.argsStatic is true when no "Args" VertexShader has ever fired for this
    // input, so _baseArgs (and therefore _points) can never have changed.
    if (!meta.argsStatic || !_geomValid) {
        _points.clear();
        buildPath(meta.args());
    }

    BP_T(t1);

    size_t n = _points.size();
    if (n < 4 || n % 2 != 0) {
        return {};
    }

    // --- Geometry cache --------------------------------------------------------
    // Key: _points bytes + scale.x/y + rotation + fill/stroke visibility.
    // Fill sampling (localPoly/earIndices) only runs when fill is non-transparent,
    // so a transparency change must bust the cache.
    size_t geomHash = fnvHash(_points.data(), n * sizeof(cv::Vec2f));
    geomHash = fnvHash(&meta.scale.x,   sizeof(float), geomHash);
    geomHash = fnvHash(&meta.scale.y,   sizeof(float), geomHash);
    geomHash = fnvHash(&meta.rotation,  sizeof(float), geomHash);
    auto anyStopVisible = [](const std::vector<GradientStop>& stops) {
        return std::any_of(stops.begin(), stops.end(), [](const GradientStop& s) { return s.color[3] > 0; });
    };
    bool hasFillNow = (_fillGradType != GradType::None) ? anyStopVisible(_fillStops) : _fillColor[3] > 0;
    geomHash = fnvHash(&hasFillNow,     sizeof(bool),  geomHash);

    if (!_geomValid || geomHash != _lastGeomHash) {
        // Build quadratic bezier segments from the anchor-handle path.
        size_t                         segCount = n / 2;
        std::vector<QuadraticBezier2D> curves;
        curves.reserve(segCount);
        for (size_t i = 0; i < segCount; ++i) {
            curves.push_back({
                _points[2 * i],
                _points[2 * i + 1],
                _points[(2 * i + 2) % n],
            });
        }

        // Bounding box of control points.
        float minX = _points[0][0], maxX = _points[0][0];
        float minY = _points[0][1], maxY = _points[0][1];
        for (const auto& p : _points) {
            minX = std::min(minX, p[0]);
            maxX = std::max(maxX, p[0]);
            minY = std::min(minY, p[1]);
            maxY = std::max(maxY, p[1]);
        }

        // Shift all control points so the bounding box starts at (0,0).
        cv::Vec2f localOffset{-minX, -minY};
        for (auto& c : curves) {
            c.p0 += localOffset;
            c.p1 += localOffset;
            c.p2 += localOffset;
        }

        cv::Size2f localSize{maxX - minX, maxY - minY};

        // Use a temporary factory just for step calculation (position doesn't
        // affect quadraticStrokeSteps, so meta.position is irrelevant here).
        MeshFactory sampleFactory(localSize, meta, config);

        // Sample the bezier path to a local-space polyline for fill tessellation.
        std::vector<cv::Vec2f> localPoly;
        if (hasFillNow) {
            for (size_t ci = 0; ci < curves.size(); ++ci) {
                int steps  = sampleFactory.quadraticStrokeSteps(curves[ci]);
                int sStart = (ci == 0) ? 0 : 1;
                int sEnd   = (_closed && ci == curves.size() - 1) ? steps - 1 : steps;
                for (int s = sStart; s <= sEnd; ++s) {
                    float t = static_cast<float>(s) / static_cast<float>(steps);
                    localPoly.push_back(MeshFactory::evalQuadratic(curves[ci], t));
                }
            }
        }

        // Fill triangulation — earcut handles non-convex polygons correctly.
        std::vector<uint16_t> earIndices;
        if (hasFillNow && localPoly.size() >= 3) {
            std::vector<std::vector<std::array<float, 2>>> polygon(1);
            polygon[0].reserve(localPoly.size());
            for (const auto& p : localPoly)
                polygon[0].push_back({p[0], p[1]});
            earIndices = mapbox::earcut<uint16_t>(polygon);
        }

        // Store in cache.
        _geomCache = GeomCache{
            std::move(localPoly),
            std::move(earIndices),
            std::move(curves),
            localSize,
        };
        _lastGeomHash = geomHash;
        _geomValid    = true;
    }

    BP_T(t2);

    // --- Mesh assembly from cached local geometry + current transform ----------
    MeshFactory factory(_geomCache.localSize, meta, config);

    // Apply meta.opacity to all colors, including each gradient stop's alpha.
    float     opacityF    = meta.opacity / 255.f;
    cv::Vec4b fillColor   = _fillColor;
    cv::Vec4b strokeColor = _strokeColor;
    fillColor[3]   = static_cast<uint8_t>(fillColor[3]   * opacityF);
    strokeColor[3] = static_cast<uint8_t>(strokeColor[3] * opacityF);

    auto applyOpacity = [opacityF](const std::vector<GradientStop>& stops) {
        std::vector<GradientStop> result = stops;
        for (auto& stop : result)
            stop.color[3] = static_cast<uint8_t>(stop.color[3] * opacityF);
        return result;
    };
    std::vector<GradientStop> fillStops   = (_fillGradType   != GradType::None) ? applyOpacity(_fillStops)   : std::vector<GradientStop>{};
    std::vector<GradientStop> strokeStops = (_strokeGradType != GradType::None) ? applyOpacity(_strokeStops) : std::vector<GradientStop>{};

    bool fillVisible   = (_fillGradType   != GradType::None) ? anyStopVisible(fillStops)   : fillColor[3] > 0;
    bool strokeVisible = (_strokeGradType != GradType::None) ? anyStopVisible(strokeStops) : strokeColor[3] > 0;
    bool hasStroke     = (_strokeWidth > 0.f && strokeVisible);

    // Local mesh-space Y is the negation of world-space Y (world is positive-up,
    // pixel/local space grows downward), so the gradient direction's sine component
    // must be negated to keep the angle convention intuitive in world terms:
    // 0° = left→right, 90° = bottom→top, counterclockwise.
    auto gradientDir = [](float angleDeg) -> cv::Vec2f {
        float angleRad = angleDeg * (static_cast<float>(M_PI) / 180.f);
        return {std::cos(angleRad), -std::sin(angleRad)};
    };

    // Emit fill vertices (applies current transform M to each local point).
    BP_T(t3);
    const auto& localPoly = _geomCache.localPoly;

    if (_fillGradType == GradType::Radial && localPoly.size() >= 3 && fillVisible) {
        // --- Radial gradient: star mesh (center fan + concentric ring strips) ---
        //
        // Ring vertices are angle-sampled and clamped to the polygon boundary via
        // boundaryDist[j] (ray-cast from center). This keeps every ring — including
        // the outermost — strictly inside (or on) the polygon, so geometry never
        // bleeds outside the shape's silhouette.
        //
        // Clamping the outermost ring to boundaryDist means it sits exactly ON the
        // polygon boundary, but the chord between two adjacent ray samples can still
        // cut inside an actual corner (leaving a black gap there). To fix that without
        // reintroducing bleed, we additionally splice in any localPoly vertices
        // ("corner extras") that fall outside the chord for that sector — these are
        // real boundary points, so they can't extend past the shape.

        cv::Vec2f center{_geomCache.localSize.width * 0.5f, _geomCache.localSize.height * 0.5f};

        float maxRadius = 0.f;
        for (const auto& p : localPoly) {
            float dx = p[0] - center[0], dy = p[1] - center[1];
            maxRadius = std::max(maxRadius, std::sqrt(dx * dx + dy * dy));
        }
        if (maxRadius < 1e-6f) maxRadius = 1e-6f;

        float pixelRadius = maxRadius * std::max(meta.scale.x, meta.scale.y);
        int   N           = std::max(24, static_cast<int>(2.f * static_cast<float>(M_PI) * pixelRadius / 6.f));
        const float TAU   = 2.f * static_cast<float>(M_PI);
        const size_t M    = localPoly.size();

        // boundaryDist[j]: distance from center to the polygon boundary along the
        // ray at angle theta_j = TAU*j/N (max intersection with any polygon edge).
        std::vector<float> boundaryDist(N);
        for (int j = 0; j < N; ++j) {
            float theta = TAU * j / N;
            cv::Vec2f d{std::cos(theta), std::sin(theta)};
            float best = 0.f;
            for (size_t ei = 0; ei < M; ++ei) {
                const cv::Vec2f& a = localPoly[ei];
                const cv::Vec2f& b = localPoly[(ei + 1) % M];
                cv::Vec2f e = b - a;
                float denom = d[0] * e[1] - d[1] * e[0];
                if (std::abs(denom) < 1e-9f) continue;
                cv::Vec2f ca = a - center;
                float t = (ca[0] * e[1] - ca[1] * e[0]) / denom;
                float s = (ca[0] * d[1] - ca[1] * d[0]) / denom;
                if (t > 1e-6f && s >= -1e-6f && s <= 1.f + 1e-6f)
                    best = std::max(best, t);
            }
            boundaryDist[j] = (best > 0.f) ? best : maxRadius;
        }

        auto ringPt = [&](int j, float r) -> cv::Vec2f {
            float theta    = TAU * j / N;
            float clampedR = std::min(r, boundaryDist[j]);
            return center + cv::Vec2f{clampedR * std::cos(theta), clampedR * std::sin(theta)};
        };

        auto radialColor = [&](cv::Vec2f pt) -> cv::Vec4b {
            float dx = pt[0] - center[0], dy = pt[1] - center[1];
            return lerpGradient(fillStops, std::sqrt(dx * dx + dy * dy) / maxRadius);
        };

        auto emitRing = [&](float r) {
            for (int j = 0; j < N; ++j) {
                cv::Vec2f pt = ringPt(j, r);
                factory.addVertex(pt[0], pt[1], radialColor(pt));
            }
        };

        // Center vertex + ring0 (degenerate to the center point unless the first
        // stop is pinned at a non-zero position).
        uint16_t centerIdx = factory.vertexCount();
        factory.addVertex(center[0], center[1], fillStops.front().color);

        uint16_t ring0Base = factory.vertexCount();
        float    ring0R    = fillStops.front().position * maxRadius;
        emitRing(ring0R);

        if (ring0R > 1e-6f) {
            for (int j = 0; j < N; ++j) {
                factory.mesh.indices.push_back(centerIdx);
                factory.mesh.indices.push_back(static_cast<uint16_t>(ring0Base + j));
                factory.mesh.indices.push_back(static_cast<uint16_t>(ring0Base + (j + 1) % N));
            }
        }

        // Pre-emit localPoly vertices once — used as "corner extras" when
        // triangulating the outermost ring strip.
        uint16_t polyBase = factory.vertexCount();
        for (const auto& p : localPoly)
            factory.addVertex(p[0], p[1], radialColor(p));

        std::vector<float> pAngle(M), pDist(M);
        for (size_t i = 0; i < M; ++i) {
            float dx = localPoly[i][0] - center[0], dy = localPoly[i][1] - center[1];
            float a  = std::atan2f(dy, dx);
            pAngle[i] = (a < 0.f) ? a + TAU : a;
            pDist[i]  = std::sqrt(dx * dx + dy * dy);
        }
        std::vector<std::vector<size_t>> sectorVerts(N);
        for (size_t i = 0; i < M; ++i) {
            int sec = static_cast<int>(pAngle[i] * N / TAU);
            sec = std::clamp(sec, 0, N - 1);
            sectorVerts[sec].push_back(i);
        }
        for (auto& sv : sectorVerts)
            std::sort(sv.begin(), sv.end(), [&](size_t a, size_t b) { return pAngle[a] < pAngle[b]; });

        // Ring-to-ring quad strips for each stop interval; the last interval also
        // splices in corner extras.
        uint16_t prevBase = ring0Base;
        for (size_t k = 0; k + 1 < fillStops.size(); ++k) {
            float rA = fillStops[k].position * maxRadius;
            float rB = fillStops[k + 1].position * maxRadius;
            if (rB <= rA + 1e-6f) continue;

            uint16_t outerBase = factory.vertexCount();
            emitRing(rB);

            bool isLast = (k + 2 == fillStops.size());

            for (int j = 0; j < N; ++j) {
                int      jn = (j + 1) % N;
                uint16_t i0 = static_cast<uint16_t>(prevBase + j);
                uint16_t i1 = static_cast<uint16_t>(prevBase + jn);
                uint16_t i2 = static_cast<uint16_t>(outerBase + j);
                uint16_t i3 = static_cast<uint16_t>(outerBase + jn);

                factory.mesh.indices.push_back(i0);
                factory.mesh.indices.push_back(i1);
                factory.mesh.indices.push_back(i2);

                if (isLast) {
                    float ringRJ  = std::min(rB, boundaryDist[j]);
                    float ringRJn = std::min(rB, boundaryDist[jn]);
                    float thresh  = std::max(ringRJ, ringRJn);

                    // Fan from i1 through the outer chain (i3, extras…, i2), where
                    // extras are localPoly vertices in this sector that lie outside
                    // the i3–i2 chord.
                    uint16_t prev = i3;
                    const auto& extras = sectorVerts[j];
                    for (auto it = extras.rbegin(); it != extras.rend(); ++it) {
                        size_t pi = *it;
                        if (pDist[pi] <= thresh + 1e-4f) continue;
                        uint16_t e = static_cast<uint16_t>(polyBase + pi);
                        factory.mesh.indices.push_back(i1);
                        factory.mesh.indices.push_back(prev);
                        factory.mesh.indices.push_back(e);
                        prev = e;
                    }
                    factory.mesh.indices.push_back(i1);
                    factory.mesh.indices.push_back(prev);
                    factory.mesh.indices.push_back(i2);
                } else {
                    factory.mesh.indices.push_back(i1);
                    factory.mesh.indices.push_back(i3);
                    factory.mesh.indices.push_back(i2);
                }
            }
            prevBase = outerBase;
        }

    } else if (_fillGradType == GradType::Conic && localPoly.size() >= 3 && fillVisible) {
        // --- Conic gradient: fan from center to the polygon boundary ---
        //
        // Color depends only on the angle around `center`, wrapped to t∈[0,1).
        // A hard "seam" is inserted at `_fillGradientAngle` (t=0 meets t=1) —
        // matching CSS conic-gradient when the first/last stop colors differ.
        //
        // Each pie-slice triangle gets its own center-vertex copy, colored to
        // match its leading edge. A single shared center vertex would blend
        // every slice toward one fixed color near the middle, creating spurious
        // "spokes" — color must stay constant along any radius.

        cv::Vec2f center{_geomCache.localSize.width * 0.5f, _geomCache.localSize.height * 0.5f};

        float maxRadius = 0.f;
        for (const auto& p : localPoly) {
            float dx = p[0] - center[0], dy = p[1] - center[1];
            maxRadius = std::max(maxRadius, std::sqrt(dx * dx + dy * dy));
        }
        if (maxRadius < 1e-6f) maxRadius = 1e-6f;

        float pixelRadius = maxRadius * std::max(meta.scale.x, meta.scale.y);
        int   N           = std::max(24, static_cast<int>(2.f * static_cast<float>(M_PI) * pixelRadius / 6.f));
        const float TAU   = 2.f * static_cast<float>(M_PI);
        const size_t M    = localPoly.size();

        // Ray-cast from center at local angle `theta` to the polygon boundary.
        auto rayDist = [&](float theta) -> float {
            cv::Vec2f d{std::cos(theta), std::sin(theta)};
            float best = 0.f;
            for (size_t ei = 0; ei < M; ++ei) {
                const cv::Vec2f& a = localPoly[ei];
                const cv::Vec2f& b = localPoly[(ei + 1) % M];
                cv::Vec2f e = b - a;
                float denom = d[0] * e[1] - d[1] * e[0];
                if (std::abs(denom) < 1e-9f) continue;
                cv::Vec2f ca = a - center;
                float t = (ca[0] * e[1] - ca[1] * e[0]) / denom;
                float s = (ca[0] * d[1] - ca[1] * d[0]) / denom;
                if (t > 1e-6f && s >= -1e-6f && s <= 1.f + 1e-6f)
                    best = std::max(best, t);
            }
            return (best > 0.f) ? best : maxRadius;
        };

        // World-space sweep angle: 0 = right, 90 = up, CCW (matches LinearGradient's
        // angle convention). Local space Y is flipped relative to world space, so
        // local angle = -world angle.
        float angleRad = _fillGradientAngle * (static_cast<float>(M_PI) / 180.f);

        auto wrapToUnit = [](float x) {
            x = std::fmod(x, 1.f);
            return (x < 0.f) ? x + 1.f : x;
        };
        auto conicT = [&](float localAngle) {
            return wrapToUnit((-localAngle - angleRad) / TAU);
        };

        // Boundary chain: N evenly-spaced ray samples + any localPoly vertices
        // that stick out beyond their sector's chord (corner extras), sorted by
        // local angle — same corner-coverage idea as the radial gradient's
        // outermost ring.
        struct ChainPt { cv::Vec2f pt; float angle; };
        std::vector<ChainPt> chain;
        chain.reserve(N + M);

        std::vector<float> boundaryDist(N);
        for (int j = 0; j < N; ++j) {
            float theta = TAU * j / N;
            boundaryDist[j] = rayDist(theta);
            chain.push_back({center + cv::Vec2f{boundaryDist[j] * std::cos(theta), boundaryDist[j] * std::sin(theta)}, theta});
        }
        for (size_t i = 0; i < M; ++i) {
            float dx = localPoly[i][0] - center[0], dy = localPoly[i][1] - center[1];
            float a    = std::atan2f(dy, dx);
            if (a < 0.f) a += TAU;
            float dist = std::sqrt(dx * dx + dy * dy);
            int j  = std::clamp(static_cast<int>(a * N / TAU), 0, N - 1);
            int jn = (j + 1) % N;
            if (dist > std::max(boundaryDist[j], boundaryDist[jn]) + 1e-4f)
                chain.push_back({localPoly[i], a});
        }
        std::sort(chain.begin(), chain.end(), [](const ChainPt& a, const ChainPt& b) { return a.angle < b.angle; });

        // Insert a hard seam at the gradient's start angle: two coincident
        // vertices, t=0 (first stop color) just before, t=1 (last stop color)
        // just after, in angular order.
        float la0 = std::fmod(-angleRad, TAU);
        if (la0 < 0.f) la0 += TAU;
        float seamR = rayDist(la0);
        cv::Vec2f seamPt = center + cv::Vec2f{seamR * std::cos(la0), seamR * std::sin(la0)};

        size_t insertAt = chain.size();
        for (size_t i = 0; i < chain.size(); ++i) {
            if (chain[i].angle > la0) { insertAt = i; break; }
        }
        chain.insert(chain.begin() + static_cast<long>(insertAt), 2, ChainPt{seamPt, la0});

        std::vector<uint16_t> chainIdx(chain.size());
        std::vector<cv::Vec4b> chainColor(chain.size());
        for (size_t i = 0; i < chain.size(); ++i) {
            if (i == insertAt)          chainColor[i] = lerpGradient(fillStops, 0.f);
            else if (i == insertAt + 1) chainColor[i] = lerpGradient(fillStops, 1.f);
            else                        chainColor[i] = lerpGradient(fillStops, conicT(chain[i].angle));
            chainIdx[i] = factory.vertexCount();
            factory.addVertex(chain[i].pt[0], chain[i].pt[1], chainColor[i]);
        }

        size_t cnt = chain.size();
        for (size_t i = 0; i < cnt; ++i) {
            uint16_t c = factory.vertexCount();
            factory.addVertex(center[0], center[1], chainColor[i]);
            factory.mesh.indices.push_back(c);
            factory.mesh.indices.push_back(chainIdx[i]);
            factory.mesh.indices.push_back(chainIdx[(i + 1) % cnt]);
        }

    } else if (fillVisible && !_geomCache.earIndices.empty()) {
        // --- Linear gradient or solid fill: earcut-based ---
        uint16_t firstPolyIdx = factory.vertexCount();

        if (_fillGradType == GradType::Linear) {
            cv::Vec2f dir = gradientDir(_fillGradientAngle);

            float minProj = std::numeric_limits<float>::max();
            float maxProj = std::numeric_limits<float>::lowest();
            for (const auto& p : localPoly) {
                float proj = p[0] * dir[0] + p[1] * dir[1];
                minProj = std::min(minProj, proj);
                maxProj = std::max(maxProj, proj);
            }
            float range = maxProj - minProj;

            if (fillStops.size() <= 2) {
                // 2-stop: color is a linear function of projection → the earcut
                // fan triangulation reproduces it exactly via GPU linear interp.
                for (const auto& p : localPoly) {
                    float proj = p[0] * dir[0] + p[1] * dir[1];
                    float t    = (range > 0.f) ? (proj - minProj) / range : 0.f;
                    factory.addVertex(p[0], p[1], lerpGradient(fillStops, t));
                }
                for (auto idx : _geomCache.earIndices)
                    factory.mesh.indices.push_back(firstPolyIdx + idx);
            } else {
                // Multi-stop: clip to each stop interval and earcut each strip.
                for (size_t k = 0; k + 1 < fillStops.size(); ++k) {
                    float projA = minProj + fillStops[k].position     * range;
                    float projB = minProj + fillStops[k + 1].position * range;
                    if (projA >= projB) continue;

                    auto strip = clipPolyHalfPlane(localPoly, dir, projA, true);
                    strip      = clipPolyHalfPlane(strip,     dir, projB, false);
                    if (strip.size() < 3) continue;

                    std::vector<std::vector<std::array<float, 2>>> stripPoly(1);
                    stripPoly[0].reserve(strip.size());
                    for (const auto& p : strip)
                        stripPoly[0].push_back({p[0], p[1]});
                    auto stripIdx = mapbox::earcut<uint16_t>(stripPoly);

                    uint16_t stripBase = factory.vertexCount();
                    for (const auto& p : strip) {
                        float proj   = p[0] * dir[0] + p[1] * dir[1];
                        float localT = (proj - projA) / (projB - projA);
                        factory.addVertex(p[0], p[1],
                            lerpColor(fillStops[k].color, fillStops[k + 1].color, localT));
                    }
                    for (auto idx : stripIdx)
                        factory.mesh.indices.push_back(stripBase + idx);
                }
            }
        } else {
            // Solid fill.
            for (const auto& p : localPoly)
                factory.addVertex(p[0], p[1], fillColor);
            for (auto idx : _geomCache.earIndices)
                factory.mesh.indices.push_back(firstPolyIdx + idx);
        }
    }

    // Stroke rendered on top of fill, extruded inward so it stays within the boundary.
    // addQuadraticStrokePath samples internally and uses M — not cached.
    BP_T(t4);
    if (hasStroke) {
        if (_strokeGradType != GradType::None) {
            cv::Vec2f dir = gradientDir(_strokeGradientAngle);
            factory.addQuadraticStrokePath(
                _geomCache.curves, _strokeWidth, strokeStops, dir, _closed, _closed);
        } else {
            factory.addQuadraticStrokePath(
                _geomCache.curves, _strokeWidth, strokeColor, _closed, _closed);
        }
    }
    BP_T(t5);

    if (BP_US(t0, t5) > 400)
        VC_LOG(std::format(
            "[bezier] buildPath:{}µs  geom:{}µs  factory:{}µs  fill:{}µs  stroke:{}µs  pts:{}\n",
            BP_US(t0, t1), BP_US(t1, t2), BP_US(t2, t3), BP_US(t3, t4), BP_US(t4, t5), n));

    return factory.generateMesh();
}
