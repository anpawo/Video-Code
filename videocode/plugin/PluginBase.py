"""Base classes for Video-Code plugins."""

from abc import ABC, abstractmethod
from typing import Any
from videocode.Constant import rgba, uint
from videocode.Global import Metadata


class PluginTransformation(ABC):
    """Base class for transformation plugins.
    
    Transformation plugins apply effects to inputs (blur, custom filters, etc.).
    """
    
    def __init__(self):
        """Initialize the transformation plugin."""
        self.plugin_type = "transformation"
        self.plugin_name = self.__class__.__name__
    
    def modificator(self, meta: Metadata) -> Metadata:
        """Modify metadata before applying transformation.
        
        Args:
            meta: Current metadata state
            
        Returns:
            Modified metadata
        """
        return meta
    
    def serialize(self) -> dict[str, Any]:
        """Serialize plugin parameters for C++ runtime.
        
        Returns:
            Dictionary of serialized parameters
        """
        return {
            "plugin_type": self.plugin_type,
            "plugin_name": self.plugin_name,
            "params": self._getParams()
        }
    
    @abstractmethod
    def _getParams(self) -> dict[str, Any]:
        """Get plugin-specific parameters.
        
        Returns:
            Dictionary of parameter name -> value
        """
        pass


class PluginInput(ABC):
    """Base class for input plugins.
    
    Input plugins provide custom input sources (shapes, patterns, etc.).
    """
    
    def __init__(self):
        """Initialize the input plugin."""
        self.plugin_type = "input"
        self.plugin_name = self.__class__.__name__
        self.index = -1  # Will be set by the system
        self.transformations = []
        
    def apply(self, transformation):
        """Apply a transformation to this input.
        
        Args:
            transformation: Transformation to apply
            
        Returns:
            Self for method chaining
        """
        self.transformations.append(transformation)
        return self
    
    def add(self, duration: uint = 1):
        """Add this input to the timeline.
        
        Args:
            duration: Number of seconds to display
        """
        from videocode.Global import addToStack
        addToStack({
            "action": "Add",
            "index": self.index,
            "duration": duration
        })
    
    def serialize(self) -> dict[str, Any]:
        """Serialize plugin for C++ runtime.
        
        Returns:
            Dictionary of serialized data
        """
        return {
            "action": "Create",
            "type": "Plugin",
            "plugin_type": self.plugin_type,
            "plugin_name": self.plugin_name,
            "params": self._getParams()
        }
    
    @abstractmethod
    def _getParams(self) -> dict[str, Any]:
        """Get plugin-specific parameters.
        
        Returns:
            Dictionary of parameter name -> value
        """
        pass
