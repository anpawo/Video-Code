"""Plugin loader for Video-Code.

This module handles discovering, loading, and registering plugins.
"""

import os
import json
import ctypes
import sys
from pathlib import Path
from typing import Dict, Any, Optional


class PluginRegistry:
    """Registry for loaded plugins."""
    
    def __init__(self):
        self.transformation_plugins: Dict[str, Any] = {}
        self.input_plugins: Dict[str, Any] = {}
        
    def registerTransformation(self, name: str, plugin_class: type):
        """Register a transformation plugin.
        
        Args:
            name: Plugin name
            plugin_class: Plugin class
        """
        self.transformation_plugins[name] = plugin_class
        
    def registerInput(self, name: str, plugin_class: type):
        """Register an input plugin.
        
        Args:
            name: Plugin name
            plugin_class: Plugin class
        """
        self.input_plugins[name] = plugin_class
    
    def getTransformation(self, name: str) -> Optional[type]:
        """Get a registered transformation plugin.
        
        Args:
            name: Plugin name
            
        Returns:
            Plugin class or None if not found
        """
        return self.transformation_plugins.get(name)
    
    def getInput(self, name: str) -> Optional[type]:
        """Get a registered input plugin.
        
        Args:
            name: Plugin name
            
        Returns:
            Plugin class or None if not found
        """
        return self.input_plugins.get(name)


# Global registry instance
_registry = PluginRegistry()


def getRegistry() -> PluginRegistry:
    """Get the global plugin registry.
    
    Returns:
        Plugin registry instance
    """
    return _registry


def loadPlugin(plugin_dir: Path, plugin_type: str) -> Optional[Dict[str, Any]]:
    """Load a single plugin from directory.
    
    Args:
        plugin_dir: Path to plugin directory
        plugin_type: 'transformation' or 'input'
        
    Returns:
        Plugin metadata or None if loading failed
    """
    json_file = plugin_dir / "plugin.json"
    
    if not json_file.exists():
        print(f"Warning: No plugin.json found in {plugin_dir}")
        return None
    
    try:
        with open(json_file, 'r') as f:
            metadata = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {json_file}: {e}")
        return None
    
    # Validate plugin type
    if metadata.get('type') != plugin_type:
        return None
    
    # Load Python library
    python_lib = plugin_dir / metadata.get('python_library', '')
    if not python_lib.exists():
        print(f"Warning: Python library not found: {python_lib}")
        return None
    
    try:
        # Load the shared library
        lib = ctypes.CDLL(str(python_lib))
        
        # Store metadata and library reference
        metadata['_lib'] = lib
        metadata['_path'] = plugin_dir
        
        print(f"Loaded plugin: {metadata['name']} v{metadata['version']}")
        return metadata
        
    except OSError as e:
        print(f"Error loading Python library {python_lib}: {e}")
        return None


def discoverPlugins(plugins_root: Path, plugin_type: str) -> list[Dict[str, Any]]:
    """Discover all plugins of a given type.
    
    Args:
        plugins_root: Root directory for plugins
        plugin_type: 'transformation' or 'input'
        
    Returns:
        List of loaded plugin metadata
    """
    if plugin_type == 'transformation':
        plugin_dir = plugins_root / 'transformations'
    elif plugin_type == 'input':
        plugin_dir = plugins_root / 'inputs'
    else:
        raise ValueError(f"Invalid plugin type: {plugin_type}")
    
    if not plugin_dir.exists():
        return []
    
    plugins = []
    for item in plugin_dir.iterdir():
        if item.is_dir():
            plugin = loadPlugin(item, plugin_type)
            if plugin:
                plugins.append(plugin)
    
    return plugins


def loadTransformationPlugins(plugins_root: Optional[Path] = None) -> int:
    """Load all transformation plugins.
    
    Args:
        plugins_root: Root directory for plugins (defaults to ./plugins)
        
    Returns:
        Number of plugins loaded
    """
    if plugins_root is None:
        plugins_root = Path.cwd() / 'plugins'
    
    plugins = discoverPlugins(plugins_root, 'transformation')
    
    for plugin in plugins:
        # Register in global namespace for easy access
        # This allows: from videocode.plugin import PluginName
        class_name = plugin['class_name']
        # Note: Actual plugin class would need to be dynamically created
        # or loaded from the shared library
        print(f"Registered transformation plugin: {class_name}")
    
    return len(plugins)


def loadInputPlugins(plugins_root: Optional[Path] = None) -> int:
    """Load all input plugins.
    
    Args:
        plugins_root: Root directory for plugins (defaults to ./plugins)
        
    Returns:
        Number of plugins loaded
    """
    if plugins_root is None:
        plugins_root = Path.cwd() / 'plugins'
    
    plugins = discoverPlugins(plugins_root, 'input')
    
    for plugin in plugins:
        class_name = plugin['class_name']
        print(f"Registered input plugin: {class_name}")
    
    return len(plugins)


def loadAllPlugins(plugins_root: Optional[Path] = None) -> tuple[int, int]:
    """Load all plugins (transformations and inputs).
    
    Args:
        plugins_root: Root directory for plugins (defaults to ./plugins)
        
    Returns:
        Tuple of (num_transformation_plugins, num_input_plugins)
    """
    num_transformations = loadTransformationPlugins(plugins_root)
    num_inputs = loadInputPlugins(plugins_root)
    return (num_transformations, num_inputs)


def getPluginMetadata(plugin_name: str, plugin_type: str, 
                       plugins_root: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """Get metadata for a specific plugin.
    
    Args:
        plugin_name: Name of the plugin
        plugin_type: 'transformation' or 'input'
        plugins_root: Root directory for plugins
        
    Returns:
        Plugin metadata or None if not found
    """
    if plugins_root is None:
        plugins_root = Path.cwd() / 'plugins'
    
    plugins = discoverPlugins(plugins_root, plugin_type)
    
    for plugin in plugins:
        if plugin['name'] == plugin_name:
            return plugin
    
    return None
