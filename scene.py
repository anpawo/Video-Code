#!/usr/bin/env python3

# A League of Legends tutorial on the template, before any footage: every Clip() without a
# file plays a labelled blank. Give a clip its file, its captions and the music to fill it in;
# videos/lol/tahm_kench.py is the same template with real footage.

from videocode import *
from videos.lol.tutorial import Clip, Section, tutorial

tutorial(
    champion="Champion",
    role="Role",
    sections=[
        Section("Advanced Combo", [
            Clip(captions=[(0.8, "the combo, key by key"), (3.5, "when it works, and when it does not")]),
            Clip(captions=[(0.8, "the same combo with flash")]),
        ]),
        Section("Laning Phase", [
            Clip(captions=[(0.8, "the first three levels")]),
            Clip(captions=[(0.8, "trading around the wave")]),
        ]),
        Section("Mid/Late Game", [
            Clip(captions=[(0.8, "your job in a teamfight")]),
        ]),
        Section("Runes", [
            Clip(seconds=5, captions=[(0.5, "the page, and why")]),
        ]),
        Section("Items", [
            Clip(seconds=5, captions=[(0.5, "the core build")]),
        ]),
    ],
    music=None,
)
