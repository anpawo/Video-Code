#!/usr/bin/env python3

#
# Transformations Types
#

# Transformation base class
from videocode.transformation.Transformation import *

# Position Template
from videocode.template.movement.moveTo import *

# Color Transformations
from videocode.transformation.color.Grayscale import *
from videocode.transformation.color.Fade import *

# Other Transformations
from videocode.transformation.size.Zoom import *
from videocode.transformation.size.Scale import *

# Setters
from videocode.transformation.setter.SetPosition import *
from videocode.transformation.setter.SetOpacity import *
from videocode.transformation.setter.SetAlign import *
