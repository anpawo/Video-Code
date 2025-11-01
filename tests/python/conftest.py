"""Test configuration for pytest"""
import pytest
import sys
import os

# Add the root directory to Python path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))