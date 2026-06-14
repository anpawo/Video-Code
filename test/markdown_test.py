#!/usr/bin/env python3

"""
Assertion-based smoke tests for `Markdown` (#76, "Markdown") —
verifies block-level parsing (headings, bullets, bold/italic paragraphs,
plain paragraphs) and that each block becomes a left-aligned `Text`.
Run directly: `python3 test/markdown_test.py`
"""

import sys

sys.path.insert(0, ".")

from videocode import Markdown
from videocode.input.shape.text._MarkdownHelper import parseMarkdown

failures: list[str] = []


def check(label: str, condition: bool):
    if condition:
        print(f"  ok   {label}")
    else:
        print(f"  FAIL {label}")
        failures.append(label)


# ── parseMarkdown ────────────────────────────────────────────────────────────
print("parseMarkdown — block-level parsing")
blocks = parseMarkdown("test/test.md", 0.4)
check("seven blocks", len(blocks) == 7)
check("h1 title text", blocks[0].text == "Title")
check("h1 bold + larger fontSize", blocks[0].bold and blocks[0].fontSize > 0.4)
check("h2 smaller than h1", blocks[1].fontSize < blocks[0].fontSize)
check("plain paragraph", blocks[2].text == "A plain paragraph." and not blocks[2].bold and not blocks[2].italic)
check("bullet items get a prefix", blocks[3].text == "• First item" and blocks[4].text == "• Second item")
check("bold paragraph", blocks[5].text == "Bold paragraph" and blocks[5].bold)
check("italic paragraph", blocks[6].text == "Italic paragraph" and blocks[6].italic)


# ── Markdown ─────────────────────────────────────────────────────────────────
print("Markdown — one Text per block, left-aligned, stacked vertically")
md = Markdown("test/test.md")
check("one Text per block (7)", len(md.inputs) == 7)
check("all left-aligned", all(t.meta.align.x == 0 for t in md.inputs))

ys = [t.meta.position.y for t in md.inputs]
check("blocks stack downward", all(ys[i] > ys[i + 1] for i in range(len(ys) - 1)))
check("bold/italic flags propagate", md.inputs[5].bold and md.inputs[6].italic)


# ── summary ──────────────────────────────────────────────────────────────────
print()
if failures:
    print(f"{len(failures)} FAILURE(S):")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)
else:
    print("All checks passed.")
