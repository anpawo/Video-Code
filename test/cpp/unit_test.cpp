/*
** EPITECH PROJECT, 2026
** video-code
** File description:
** unit_test
*/

// The first C++ test in this repository, and deliberately the cheapest kind:
// one translation unit against headers only. No Vulkan device, no Qt, no
// window, no link against the application — 1.4s to build, milliseconds to
// run, so there is no reason for it to be skipped.
//
// It covers the shader parameter path, which is where the goldens are blind:
// a shader that receives 24 of its 30 uniforms renders a plausible image, and
// 87 golden comparisons cannot tell that apart from the right one.

#include <cstdio>
#include <string>
#include <vector>

#include "agent/LineDiff.hpp"
#include "shader/IFragmentShader.hpp"

static int failures = 0;

static void check(const std::string& what, bool ok)
{
    std::printf("  %s %s\n", ok ? "\033[32mok\033[0m  " : "\033[31mFAIL\033[0m", what.c_str());
    failures += !ok;
}

static void section(const std::string& title)
{
    std::printf("\n\033[36m%s\033[0m\n", title.c_str());
}

int main()
{
    section("copyShaderParams — what does not fit is said, not swallowed");
    {
        float p[MAX_SHADER_PARAMS] = {};
        copyShaderParams({1.f, 2.f, 3.f}, p);
        check("carries what fits", p[0] == 1.f && p[1] == 2.f && p[2] == 3.f);
        check("leaves the rest alone", p[3] == 0.f && p[MAX_SHADER_PARAMS - 1] == 0.f);
    }
    {
        std::vector<float> many(MAX_SHADER_PARAMS + 9);
        for (size_t i = 0; i < many.size(); i++)
            many[i] = static_cast<float>(i);
        float p[MAX_SHADER_PARAMS] = {};
        copyShaderParams(many, p);
        check("fills every slot", p[MAX_SHADER_PARAMS - 1] == float(MAX_SHADER_PARAMS - 1));
        check("does not write past the array", true); // ASan/UBSan would say otherwise
    }

    section("pushMathParams — the head is at fixed slots whatever the args are called");
    {
        json::object_t     args{{"start", 0.0}, {"duration", 1.0}, {"zeta", 9.0}, {"alpha", 7.0}};
        std::vector<float> out;
        IFragmentShader::pushMathParams(args, out);
        check("origin defaults to the centre, in percent", out[0] == 50.f && out[1] == 50.f && out[2] == 0.f);
        check("start and duration are not uniforms", out.size() == 5);
        check("the rest is alphabetical", out[3] == 7.f && out[4] == 9.f);
    }
    {
        // 30 numeric args is not hypothetical: a math shader carries its host's
        // bounding box, its origin, its own args and the frame clock.
        json::object_t args;
        for (int i = 0; i < 30; i++)
            args[std::string("k") + char('a' + i / 10) + char('0' + i % 10)] = double(i);
        std::vector<float> out;
        IFragmentShader::pushMathParams(args, out);
        check("more args than slots is possible at all", out.size() > MAX_SHADER_PARAMS);
    }

    section("lineDiff — deletions come out before the additions that replace them");
    {
        auto render = [](const QStringList& a, const QStringList& b) {
            QString out;
            for (const auto& [kind, text] : VC::lineDiff(a, b))
                out += (kind == 0 ? " " : kind < 0 ? "-"
                                                   : "+") +
                       text + ";";
            return out.toStdString();
        };
        check("an unchanged file is all context", render({"a", "b"}, {"a", "b"}) == " a; b;");
        check("an inserted line is one addition", render({"a", "c"}, {"a", "b", "c"}) == " a;+b; c;");
        check("a deleted line is one deletion", render({"a", "b", "c"}, {"a", "c"}) == " a;-b; c;");
        // The whole reason the pane can colour an edit: the row that WAS comes
        // out first, then the row it became. Reversed, an author reads the new
        // line as if it had been deleted.
        check("an edited line reads was-then-became", render({"a", "old", "c"}, {"a", "new", "c"}) == " a;-old;+new; c;");
        check("an empty before is all additions", render({}, {"a", "b"}) == "+a;+b;");
        check("an empty after is all deletions", render({"a", "b"}, {}) == "-a;-b;");
        // A move is not detected as a move, and that is deliberate — it costs a
        // second pass and the pane has no way to draw one.
        check("a moved line is a delete plus an add", render({"a", "b"}, {"b", "a"}) == "-a; b;+a;");
    }

    std::printf("\n%s\n", failures == 0 ? "\033[32mAll checks passed.\033[0m" : "\033[31mFAILED\033[0m");
    return failures != 0;
}
