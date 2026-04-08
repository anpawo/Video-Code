#!/usr/bin/env python3


from videocode.template.misc.example.marius import *
from videocode.videocode import *

### Marius' Test (Do not remove, just comment it)
# example3()


r = Rectangle().flush()
wait(1)
r.easeTo(30, "cornerRadius", duration=1).flush()
