"""Gradient input plugin for Video-Code.

This plugin generates gradient backgrounds.
"""

import sys
import os

# Add videocode to path if running as plugin
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from videocode.plugin.PluginBase import PluginInput
from videocode.Constant import rgba, RED, BLUE
from typing import Any


class Gradient(PluginInput):
    """Generates gradient backgrounds."""
    
    def __init__(self, color1: rgba = RED, color2: rgba = BLUE, 
                 direction: str = "horizontal"):
        """Initialize gradient input.
        
        Args:
            color1: Start color (RGBA)
            color2: End color (RGBA)
            direction: Gradient direction (horizontal, vertical, diagonal)
        """
        super().__init__()
        self.color1 = color1
        self.color2 = color2
        self.direction = direction
        
        # Register this input in the global system
        from videocode.Global import addToStack, getNextIndex
        self.index = getNextIndex()
        
        # Add creation action to stack
        addToStack(self.serialize())
    
    def _getParams(self) -> dict[str, Any]:
        """Get plugin parameters for serialization."""
        return {
            "color1": list(self.color1),
            "color2": list(self.color2),
            "direction": self.direction,
            "index": self.index
        }


# Plugin factory functions
def create(color1: rgba = RED, color2: rgba = BLUE, 
          direction: str = "horizontal") -> Gradient:
    """Create gradient plugin instance.
    
    Args:
        color1: Start color
        color2: End color
        direction: Gradient direction
        
    Returns:
        Gradient plugin instance
    """
    return Gradient(color1, color2, direction)


def destroy(instance: Gradient) -> None:
    """Destroy gradient plugin instance.
    
    Args:
        instance: Plugin instance to destroy
    """
    del instance
