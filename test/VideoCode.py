#!/usr/bin/env python3


from abc import ABC


class Globals:
    """
    Globals used by the classes `Input` and `Transformation`.
    """

    # Video or Images to import
    input = []

    # Variables declared in a scene
    variable = []

    # Represents the steps of the scene
    stack = []


class Scene(ABC):
    """
    Parent class for scenes.

    Needed to filter out classes made by the user for anything else other than a `Scene`.
    """

    __input = Globals.input
    __variable = Globals.variable
    __stack = Globals.stack
