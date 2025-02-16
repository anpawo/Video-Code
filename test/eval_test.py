#!/usr/bin/env python3


# from frontend.VideoCode import *

s = r"""


def test():
    z = 0
    print(z, end="\n\n")  # ❌ NameError: z is not defined


test()
"""

print(globals(), end="\n\n")
exec(s)
print(globals(), end="\n\n")
