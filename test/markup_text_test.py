#!/usr/bin/env python3

"""
Assertion-based smoke tests for `MarkupText` — verifies that `<b>`/`<i>`/
`<font color>` style the run they wrap instead of being drawn as glyphs, that
a run is shaped with its own face (so a bold word advances by bold widths),
and that a text with no markup lays out exactly like the `Text` it used to be.
Run directly: `python3 test/markup_text_test.py`
"""

import sys
import tempfile

sys.path.insert(0, ".")
sys.path.insert(0, "test")
from helpers import check, section, summary

from videocode import RED_B, MarkupText, Subtitles, Text, bold, colored, italic, rgba
from videocode.input.shape.text._MarkdownHelper import parseMarkdown
from videocode.input.shape.text._TextHelper import parseMarkup

# ── parseMarkup ──────────────────────────────────────────────────────────────
section("parseMarkup — tags become runs, everything else is dropped")
plain, runs = parseMarkup('a <b>b</b> <font color="#FF6A00">c</font>')
check("the tags leave the text", plain == "a b c")
check("one run per styled slice, in plain-character indices", [(r[0], r[1], r[2]) for r in runs] == [(2, 3, True), (4, 5, False)])
check("the colour is read off the tag", runs[1][4] == rgba("#FF6A00"))

check("an unknown tag is stripped, not drawn", parseMarkup("<u>a</u>")[0] == "a")
check("an ASS override block is stripped too", parseMarkup(r"{\an8}a")[0] == "a")
check("no markup means no run at all", parseMarkup("plain")[1] == ())
check("nesting ORs the styles", parseMarkup("<b><i>x</i></b>")[1] == ((0, 1, True, True, None),))
check("an unclosed tag runs to the end", parseMarkup("a<b>bc")[1] == ((1, 3, True, False, None),))

# ── MarkupText ───────────────────────────────────────────────────────────────
section("MarkupText — the tags style the letters instead of becoming letters")
t = MarkupText("a <b>b</b> c")
check("`.text` is the plain text", t.text == "a b c")
check("three letters, not ten", len(t.inputs) == 3)
check("only the wrapped letter is bold", [l.bold for l in t.inputs] == [False, True, False])
check("`<i>` does the same to italic", [l.italic for l in MarkupText("a <i>b</i> c").inputs] == [False, True, False])

red = MarkupText('x <font color="#ff0000">red</font>')
check("a colour run paints its own letters", [l.fillColor == rgba("#ff0000") for l in red.inputs] == [False, True, True, True])
red.fillColor = rgba("#00ff00")
check("assigning fillColor still overrides every run", all(l.fillColor == rgba("#00ff00") for l in red.inputs))

check("a run's bold ORs with the base italic", all(l.bold and l.italic for l in MarkupText("<b>x</b>", italic=True).inputs))

# ── bold | "x" ───────────────────────────────────────────────────────────────
section("bold | 'x' — the tag written for you, the engine sees the hand-written one")


def sameLetters(a: MarkupText, b: MarkupText) -> bool:
    return [(l.char, l.bold, l.italic, l.fillColor, l.meta.position.x) for l in a.inputs] == [
        (l.char, l.bold, l.italic, l.fillColor, l.meta.position.x) for l in b.inputs
    ]


check("bold | 'x' is <b>x</b>", sameLetters(MarkupText(f"a {bold | 'bc'} d"), MarkupText("a <b>bc</b> d")))
check("italic | 'x' is <i>x</i>", sameLetters(MarkupText(f"a {italic | 'bc'} d"), MarkupText("a <i>bc</i> d")))
check(
    "colored(RED_B) | 'x' is <font color>x</font>",
    sameLetters(MarkupText(f"a {colored(RED_B) | 'bc'} d"), MarkupText('a <font color="#ED7F7B">bc</font> d')),
)
check("colored takes a '#RRGGBB' too", (colored("#ED7F7B") | "x") == (colored(RED_B) | "x"))
check("bold | italic | 'x' nests both", sameLetters(MarkupText(f"a {bold | italic | 'bc'} d"), MarkupText("a <b><i>bc</i></b> d")))
check("bold('x') is bold | 'x'", bold("x") == (bold | "x"))

esc = MarkupText(f"if {bold | 'a<b'} then")
check("a < in the wrapped text is a letter, not a tag", esc.text == "if a<b then" and [l.bold for l in esc.inputs] == [False] * 2 + [True] * 3 + [False] * 4)
check("an & survives too", MarkupText(bold | "a & b").text == "a & b")

three = MarkupText(f"{bold | 'ab'} {italic | 'cd'} {colored(RED_B) | 'ef'}")
# Six letters: a space has no glyph, so it is no `Letter`.
check("three styles in one f-string land in their own places", [(l.bold, l.italic, l.fillColor == RED_B) for l in three.inputs] == [(True, False, False)] * 2 + [(False, True, False)] * 2 + [(False, False, True)] * 2)

try:
    bold | "x" | italic  # type: ignore[operator]
    check("bold | 'x' | italic fails out loud", False)
except TypeError:
    check("bold | 'x' | italic fails out loud", True)

# ── layout ───────────────────────────────────────────────────────────────────
section("layout — no run shapes exactly as before, a run shapes with its own face")
check("no markup lays out like a Text", MarkupText("ab").inputs[1].meta.position.x == Text("ab").inputs[1].meta.position.x)
check(
    "a full-line run lays out like a bold Text",
    [l.meta.position.x for l in MarkupText("<b>ab</b>").inputs] == [l.meta.position.x for l in Text("ab", bold=True).inputs],
)

mixed = MarkupText("l<b>l</b>")
check("a bold run's wider advance moves the line", mixed.inputs[1].meta.position.x != Text("ll").inputs[1].meta.position.x)
check("the bold letter is the bold glyph", mixed.inputs[1].width == Text("l", bold=True).inputs[0].width)

check("a newline still opens a line", MarkupText("<b>a</b>\nb").inputs[1].meta.position.y < MarkupText("<b>a</b>\nb").inputs[0].meta.position.y)

# ── Subtitles ────────────────────────────────────────────────────────────────
section("Subtitles — a cue's markup is styling, not text")
sub = Subtitles("test/test_tags.srt")
check("`<i>Hello</i> world` is 10 letters, not 17", sub.inputs[0].text == "Hello world" and len(sub.inputs[0].inputs) == 10)
check("only the wrapped word is italic", [l.italic for l in sub.inputs[0].inputs] == [True] * 5 + [False] * 5)

loud = sub.inputs[1]
check(r"`{\an8}<b>Loud</b> <font color>red</font>` is 7 letters, not 48", loud.text == "Loud red" and len(loud.inputs) == 7)
check("the font tag paints r, e and d", [l.fillColor == rgba("#ff0000") for l in loud.inputs] == [False] * 4 + [True] * 3)
check("`<u>` is dropped rather than drawn", sub.inputs[2].text == "Plain after all")

# ── Markdown ─────────────────────────────────────────────────────────────────
section("Markdown — inline styling mixed inside one line")
with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
    f.write("Hello **bold**\n")
blocks = parseMarkdown(f.name, 0.4)
check("one block, its asterisks turned into markup", len(blocks) == 1 and blocks[0].text == "Hello <b>bold</b>")
check("the bold word is the only bold run", [l.bold for l in MarkupText(blocks[0].text).inputs] == [False] * 5 + [True] * 4)

# ── summary ──────────────────────────────────────────────────────────────────
summary()
