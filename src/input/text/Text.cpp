/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Text
*/

#include "input/text/Text.hpp"

#include <string>

#include "vulkan/MeshFactory.hpp"

#ifndef FONT_DIR
    #define FONT_DIR "assets/fonts"
#endif

Text::Text(json::object_t &&args)
    : AInput(std::move(args))
{
}

GlyphCache &Text::glyphCache()
{
    static GlyphCache cache(std::string(FONT_DIR) + "/Inter-Regular.ttf");
    return cache;
}

Mesh Text::getMesh(const Metadata &meta, const Config &config)
{
    const std::string &text = meta.args().at("text").get<std::string>();
    float              fontSize = meta.args().at("fontSize").get<float>() * config::worldToPixelRatio;
    cv::Vec4b          color = colorFromJson(meta.args().at("fillColor"), meta.opacity);

    GlyphCache &cache = glyphCache();
    float       ascender = cache.ascender() * fontSize;
    float       descender = cache.descender() * fontSize;
    float       lineHeight = ascender + descender;

    // Measure total width
    float totalWidth = 0.f;
    for (unsigned char c : text) {
        totalWidth += cache.get(c).advance * fontSize;
    }

    MeshFactory factory({totalWidth, lineHeight}, meta, config);

    float cursorX = 0.f;

    for (unsigned char c : text) {
        const GlyphMesh &g = cache.get(c);
        uint16_t         base = factory.vertexCount();

        for (const auto &v : g.vertices) {
            // v[1] is negative above baseline, positive below — shift by ascender
            float x = cursorX + v[0] * fontSize;
            float y = ascender + v[1] * fontSize;
            factory.addVertex(x, y, color);
        }

        for (auto idx : g.indices) {
            factory.addIndex(base + static_cast<uint16_t>(idx));
        }

        cursorX += g.advance * fontSize;
    }

    return factory.generateMesh();
}
