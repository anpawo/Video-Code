#!/usr/bin/env python3

from videocode import *
from videocode.template.input.YStack import Paragraphe
from videocode.template.input._inputs import *
from videocode.template.effect.other.highlight import highlight

sv = SplitView()

para = Paragraphe(gap=0.18).position(x=sv.a.left, y=sv.a.top)

para.add(Code("from videocode import *"))
para.newline()
para.add(r := Code("r = Rectangle(width=3, height=2)"))

for g in r.wait(1).find("width=3"):
    for letter in g:
        letter.apply(*highlight(letter))
# para.add(Code("r = Rectangle(width=3, height=2)"))

# bg — created last so drift() starts at the end of existing content
p = Plane().drift()
