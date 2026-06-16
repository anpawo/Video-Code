#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path


__all__ = [
    "texToSVG",
]


_CACHE_DIR = Path(__file__).resolve().parents[4] / ".cache" / "tex"

_PREAMBLE = r"""\documentclass[preview]{standalone}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{amsmath}
\usepackage{amssymb}
\begin{document}
%s
\end{document}
"""


def texToSVG(tex: str, mathMode: bool = True) -> str:
    """
    Compiles `tex` to an SVG via `latex` + `dvisvgm --no-fonts` (every glyph
    becomes an outlined `<path>`, no embedded fonts) and returns the filepath
    to the result, cached under `.cache/tex/<hash>.svg`.

    `mathMode=True` (default) wraps `tex` in `$...$`; `mathMode=False` (used
    by `Tex`) inserts `tex` verbatim as the document body.
    """
    body = f"${tex}$" if mathMode else tex
    source = _PREAMBLE % body

    digest = hashlib.sha256(source.encode()).hexdigest()
    svgPath = _CACHE_DIR / f"{digest}.svg"
    if svgPath.exists():
        return str(svgPath)

    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    texPath = _CACHE_DIR / f"{digest}.tex"
    texPath.write_text(source)

    try:
        result = subprocess.run(
            ["latex", "-interaction=batchmode", "-halt-on-error", f"-output-directory={_CACHE_DIR}", str(texPath)],
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as e:
        raise FileNotFoundError("`latex` not found — install a LaTeX distribution (see docs/SETUP_LINUX.md) to use MathTex/Tex.") from e

    if result.returncode != 0:
        logPath = _CACHE_DIR / f"{digest}.log"
        log = logPath.read_text(errors="replace") if logPath.exists() else result.stdout
        raise RuntimeError(f"latex failed to compile {tex!r}:\n{log[-2000:]}")

    dviPath = _CACHE_DIR / f"{digest}.dvi"
    try:
        result = subprocess.run(
            ["dvisvgm", "--no-fonts", "-o", str(svgPath), str(dviPath)],
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as e:
        raise FileNotFoundError("`dvisvgm` not found — install a LaTeX distribution with dvisvgm (see docs/SETUP_LINUX.md) to use MathTex/Tex.") from e

    if result.returncode != 0:
        raise RuntimeError(f"dvisvgm failed to convert {tex!r}:\n{result.stderr[-2000:]}")

    return str(svgPath)
