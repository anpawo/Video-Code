#!/usr/bin/env python3

"""F16 — markup written inside an f-string, and text that stays escaped."""

from videocode import *

MarkupText(markup=f"one word in {bold | 'bold'}, one in {colored(RED_B) | 'red'}", fontSize=0.55).position(0, 1)
MarkupText(markup=f"{bold | 'a < b'} keeps its bracket", fontSize=0.55).position(0, 0)
MarkupText(markup=f"{(bold | (italic | 'both'))} at once", fontSize=0.55).position(0, -1)
wait(2)
