#!/usr/bin/env python3

#
# Transformations Types
#

# Transformation base class
from videocode.transformation.Transformation import *

# Color Transformations
from videocode.transformation.effect.Grayscale import *
from videocode.transformation.effect.Fade import *

# Other Transformations
from videocode.transformation.transformation.Scale import *

# Setters
from videocode.transformation.transformation.Position import *
from videocode.transformation.transformation.Align import *

# Template
from videocode.template.movement.moveTo import *
