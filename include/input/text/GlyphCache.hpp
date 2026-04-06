/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** GlyphCache
*/

#pragma once

#include <ft2build.h>
#include FT_FREETYPE_H
#include FT_OUTLINE_H
#include <mapbox/earcut.hpp>

#include <array>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>

struct GlyphMesh
{
    // Normalized vertices: x in [0..advance], y=0 at baseline,
    // negative y = above baseline, positive y = below baseline (screen-space)
    std::vector<std::array<float, 2>> vertices;
    std::vector<uint32_t>             indices;
    float                             advance;  ///< horizontal advance, normalized by unitsPerEm
    float                             bearingY; ///< ascent above baseline, normalized
};

class GlyphCache
{
public:

    explicit GlyphCache(const std::string &fontPath)
    {
        if (FT_Init_FreeType(&m_library)) {
            throw std::runtime_error("FreeType init failed");
        }
        if (FT_New_Face(m_library, fontPath.c_str(), 0, &m_face)) {
            throw std::runtime_error("Failed to load font: " + fontPath);
        }
        m_unitsPerEm = static_cast<float>(m_face->units_per_EM);
    }

    ~GlyphCache()
    {
        FT_Done_Face(m_face);
        FT_Done_FreeType(m_library);
    }

    const GlyphMesh &get(uint32_t codepoint)
    {
        auto it = m_cache.find(codepoint);
        if (it != m_cache.end()) {
            return it->second;
        }
        m_cache[codepoint] = triangulate(codepoint);
        return m_cache[codepoint];
    }

    float ascender()  const { return  m_face->ascender  / m_unitsPerEm; }
    float descender() const { return -m_face->descender / m_unitsPerEm; } ///< positive value

private:

    // ── Outline decomposition context ────────────────────────────────────────

    struct OutlineCtx
    {
        std::vector<std::vector<std::array<float, 2>>> contours;
        std::vector<std::array<float, 2>>              current;
        float                                          scale;
    };

    static int ftMoveTo(const FT_Vector *to, void *user)
    {
        auto *ctx = static_cast<OutlineCtx *>(user);
        if (!ctx->current.empty()) {
            ctx->contours.push_back(std::move(ctx->current));
            ctx->current.clear();
        }
        ctx->current.push_back({to->x * ctx->scale, -to->y * ctx->scale});
        return 0;
    }

    static int ftLineTo(const FT_Vector *to, void *user)
    {
        auto *ctx = static_cast<OutlineCtx *>(user);
        ctx->current.push_back({to->x * ctx->scale, -to->y * ctx->scale});
        return 0;
    }

    static int ftConicTo(const FT_Vector *ctrl, const FT_Vector *to, void *user)
    {
        auto *ctx = static_cast<OutlineCtx *>(user);
        auto &cur = ctx->current;
        float x0 = cur.back()[0], y0 = cur.back()[1];
        float x1 = ctrl->x * ctx->scale, y1 = -ctrl->y * ctx->scale;
        float x2 = to->x   * ctx->scale, y2 = -to->y   * ctx->scale;
        for (int i = 1; i <= 32; i++) {
            float t = float(i) / 32.f, mt = 1.f - t;
            cur.push_back({mt * mt * x0 + 2 * mt * t * x1 + t * t * x2,
                           mt * mt * y0 + 2 * mt * t * y1 + t * t * y2});
        }
        return 0;
    }

    static int ftCubicTo(const FT_Vector *c1, const FT_Vector *c2, const FT_Vector *to, void *user)
    {
        auto *ctx = static_cast<OutlineCtx *>(user);
        auto &cur = ctx->current;
        float x0 = cur.back()[0], y0 = cur.back()[1];
        float x1 = c1->x * ctx->scale, y1 = -c1->y * ctx->scale;
        float x2 = c2->x * ctx->scale, y2 = -c2->y * ctx->scale;
        float x3 = to->x  * ctx->scale, y3 = -to->y  * ctx->scale;
        for (int i = 1; i <= 32; i++) {
            float t = float(i) / 32.f, mt = 1.f - t;
            cur.push_back({mt*mt*mt*x0 + 3*mt*mt*t*x1 + 3*mt*t*t*x2 + t*t*t*x3,
                           mt*mt*mt*y0 + 3*mt*mt*t*y1 + 3*mt*t*t*y2 + t*t*t*y3});
        }
        return 0;
    }

    // ── Triangulation ─────────────────────────────────────────────────────────

    static float signedArea(const std::vector<std::array<float, 2>> &pts)
    {
        float area = 0.f;
        for (size_t i = 0, n = pts.size(); i < n; i++) {
            size_t j = (i + 1) % n;
            area += pts[i][0] * pts[j][1] - pts[j][0] * pts[i][1];
        }
        return area / 2.f;
    }

    GlyphMesh triangulate(uint32_t codepoint)
    {
        uint32_t idx = FT_Get_Char_Index(m_face, codepoint);
        if (FT_Load_Glyph(m_face, idx, FT_LOAD_NO_SCALE | FT_LOAD_NO_BITMAP)) {
            return {};
        }

        FT_GlyphSlot slot  = m_face->glyph;
        float        scale = 1.f / m_unitsPerEm;

        // Whitespace / no outline
        if (slot->outline.n_contours == 0) {
            return GlyphMesh{{}, {}, slot->advance.x * scale, 0.f};
        }

        OutlineCtx ctx;
        ctx.scale = scale;

        FT_Outline_Funcs funcs{ftMoveTo, ftLineTo, ftConicTo, ftCubicTo, 0, 0};
        FT_Outline_Decompose(&slot->outline, &funcs, &ctx);
        if (!ctx.current.empty()) {
            ctx.contours.push_back(std::move(ctx.current));
        }

        // Group: positive area = outer contour, negative area = hole of previous outer
        using Ring    = std::vector<std::array<float, 2>>;
        using Polygon = std::vector<Ring>;
        std::vector<Polygon> polygons;

        for (auto &contour : ctx.contours) {
            if (signedArea(contour) > 0.f || polygons.empty()) {
                polygons.push_back({contour});
            } else {
                polygons.back().push_back(contour);
            }
        }

        GlyphMesh mesh;
        mesh.advance  = slot->advance.x * scale;
        mesh.bearingY = slot->metrics.horiBearingY * scale;

        for (const auto &poly : polygons) {
            uint32_t base = static_cast<uint32_t>(mesh.vertices.size());

            for (const auto &ring : poly) {
                for (const auto &pt : ring) {
                    mesh.vertices.push_back(pt);
                }
            }

            auto triIndices = mapbox::earcut<uint32_t>(poly);
            for (auto triIdx : triIndices) {
                mesh.indices.push_back(base + triIdx);
            }
        }

        return mesh;
    }

    FT_Library m_library{};
    FT_Face    m_face{};
    float      m_unitsPerEm = 1.f;
    std::unordered_map<uint32_t, GlyphMesh> m_cache;
};
