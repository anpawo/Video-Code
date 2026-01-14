"""Plugin system for Video-Code.

This module provides the infrastructure for loading and managing plugins.
"""

from .PluginLoader import loadTransformationPlugins, loadInputPlugins, loadAllPlugins

__all__ = ['loadTransformationPlugins', 'loadInputPlugins', 'loadAllPlugins']
