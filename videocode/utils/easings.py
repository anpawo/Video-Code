#!/usr/bin/env python3


from videocode.utils.bezier import cubicBezier


class Easing:
    Linear = cubicBezier(0.0, 0.0, 1.0, 1.0)
    In = cubicBezier(0.42, 0.0, 1.0, 1.0)
    Out = cubicBezier(0.0, 0.0, 0.58, 1.0)
    InOut = cubicBezier(0.42, 0.0, 0.58, 1.0)
