import math


def frameIndex(t: float, framerate: int) -> int:
    whole = math.floor(t * framerate + 0.5)
    return int(whole)
