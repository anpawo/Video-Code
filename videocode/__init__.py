#!/usr/bin/env python3

from __future__ import annotations

#
# VideoCode
#


from videocode.ty import *
from videocode.constants import *
from videocode.context import *
from videocode.input._inputs import *
from videocode.shader._shaders import *

# `easing=CubicBezier(0.42, 0, 0.58, 1)` is what the editor's curve writes, and
# a scene has to be able to run the line it just wrote: the name belongs in the
# same scope `Easing` already reaches by way of the inputs.
from videocode.utils.bezier import CubicBezier
