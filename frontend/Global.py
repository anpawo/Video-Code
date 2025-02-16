#!/usr/bin/env python3


type Arguments = list[int | float | str | Arguments]
type Variable = list[tuple[str, Arguments]]
type Stack = list[tuple[str, int, Arguments]]


class Global:
    """
    Globals used by the classes `Input` and `Transformation`.
    """

    # Input Variables declared in a scene.
    variable: Variable = []

    # Represents the steps of the scene.
    stack: Stack = []

    def __str__(self) -> str:
        return f"\nvariable={self.variable};\n\nstack={self.stack};\n"

    def __repr__(self) -> str:
        return str(self)
