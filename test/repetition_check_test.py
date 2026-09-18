#!/usr/bin/env python3
"""
`test/repetition_check.py` on code written for the purpose: what it matches,
what it calls the same clone, and when the record says no.
"""
import sys

sys.path.insert(0, "test")

from helpers import check, section, summary  # noqa: E402
from repetition_check import clones, declared, verdict  # noqa: E402


def code(*names: str) -> list[tuple[int, str]]:
    return [(n, f"{name} = compute({name})") for n, name in enumerate(names, 1)]


shared = [f"s{i}" for i in range(21)]

section("A run is matched by the clone it belongs to")
# A holds 21 lines; B copied the first 15, C the last 15. The two copies overlap
# inside A — merged into one run of 21 there, it matched neither and all three
# were dropped.
found = clones(
    {
        "a": code(*shared),
        "b": code("b0", *shared[:15], "b1"),
        "c": code("c0", *shared[6:], "c1"),
    }
)
spots = sorted(tuple(s[0] for s in g) + (g[0][3],) for g in found.values())
check("A↔B is 15 lines", ("a", "b", 15) in spots)
check("A↔C is 15 lines", ("a", "c", 15) in spots)
check("B↔C is the 9 in the middle — A holds them too, inside the two longer ones", ("b", "c", 9) in spots)
check("nothing else", len(spots) == 3)

section("An identity does not move with the file")
before = clones({"a": code(*shared[:10]), "b": code(*shared[:10])})
after = clones({"a": code("x", "y", "z", *shared[:10]), "b": code(*shared[:10])})
check("three lines added above a clone leave its identity alone", list(before) == list(after))
check("and its position follows", next(iter(after.values()))[0][1] == 4)

section("What is not a copy")
braces = [(n, "}") for n in range(1, 13)]
check("twelve closing braces in two files", clones({"a": list(braces), "b": list(braces)}) == {})
table = [(n, "0.0f, 0.0f,") for n in range(1, 13)]
check("a table of identical lines against itself", clones({"a": table}) == {})

section("Declared twins")
pair = {"src/window/VulkanWidget.cpp", "src/vulkan/VulkanHeadlessRenderer.cpp"}
check("the two renderers", declared(pair) != "")
check("one of them copying itself is not the pair", declared({"src/window/VulkanWidget.cpp"}) == "")
check("a third file takes it out of the pair", declared(pair | {"include/vulkan/VulkanHelpers.hpp"}) == "")
check("two effect shaders", declared({"assets/shaders/sepia/frag.glsl", "assets/shaders/invert/frag.glsl"}) != "")

section("The record")
was = {"clones": {"aa": [10, 2, "x"], "bb": [30, 2, "y"]}, "twins": {"T": {"t1": [40, 2, "z"]}}}


def now(clonesNow: dict, twin: dict) -> dict:
    return {"clones": clonesNow, "twins": {"T": twin}}


new, grown, gone = verdict(was, now({"cc": [8, 2, "w"]}, was["twins"]["T"]))
check("a new clone fails even when the total falls from 40 lines to 8", new == ["cc"])
new, grown, gone = verdict(was, now({"aa": [10, 3, "x"]}, was["twins"]["T"]))
check("a third copy of a known clone is new", new == ["aa"])
new, grown, gone = verdict(was, now(was["clones"], {"t2": [40, 2, "z"]}))
check("a twin fixed on both sides: new hash, same size — silent", (new, grown, gone) == ([], [], []))
new, grown, gone = verdict(was, now(was["clones"], {"t2": [41, 2, "z"]}))
check("a twin that grows fails", [g[:3] for g in grown] == [("T", 40, 41)])
new, grown, gone = verdict(was, now(was["clones"], {"t3": [19, 2, "z"], "t4": [20, 2, "q"]}))
check("a twin fixed on one side splits in two: a warning, not a failure", (new, grown, gone) == ([], [], [("T", 40, "z")]))

summary()
