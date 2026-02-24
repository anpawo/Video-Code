#!/usr/bin/env python3


#
# VideoCode
#


# Types
from videocode.ty import *

# Constant
from videocode.constants import *

# Global
from videocode.globals import *

# Base input/shader interfaces
from videocode.input.input import *
from videocode.shader.ishader import *

# Plugin symbols
from videocode.plugin_loader import load_python_plugins

load_python_plugins(globals())
