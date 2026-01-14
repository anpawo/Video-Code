"""Blur transformation plugin for Video-Code.

This plugin applies Gaussian blur to input frames.
"""

import sys
import os

# Add videocode to path if running as plugin
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from videocode.plugin.PluginBase import PluginTransformation
from videocode.Global import Metadata
from typing import Any


class Blur(PluginTransformation):
    """Applies Gaussian blur effect to inputs."""
    
    def __init__(self, kernel_size: int = 5, sigma: float = 0.0):
        """Initialize blur effect.
        
        Args:
            kernel_size: Size of blur kernel (must be odd)
            sigma: Standard deviation for Gaussian kernel (0 = auto)
        """
        super().__init__()
        
        # Ensure kernel size is odd
        if kernel_size % 2 == 0:
            kernel_size += 1
        
        self.kernel_size = kernel_size
        self.sigma = sigma
    
    def modificator(self, meta: Metadata) -> Metadata:
        """No metadata modifications needed for blur."""
        return meta
    
    def _getParams(self) -> dict[str, Any]:
        """Get plugin parameters for serialization."""
        return {
            "kernel_size": self.kernel_size,
            "sigma": self.sigma
        }


# Plugin factory functions for Python ctypes loading
def create(kernel_size: int = 5, sigma: float = 0.0) -> Blur:
    """Create blur plugin instance.
    
    Args:
        kernel_size: Size of blur kernel
        sigma: Gaussian sigma
        
    Returns:
        Blur plugin instance
    """
    return Blur(kernel_size, sigma)


def destroy(instance: Blur) -> None:
    """Destroy blur plugin instance.
    
    Args:
        instance: Plugin instance to destroy
    """
    del instance
