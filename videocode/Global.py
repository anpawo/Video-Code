#!/usr/bin/env python3


type Arguments = dict[str, int | float | str | dict[str, Arguments] | list[Arguments]]
type RequiredInput = Arguments
type ActionStack = Arguments


class Global:
    """
    Globals used by the classes `Input` and `Transformation`.
    """

    # Input Variables declared in a scene.
    requiredInputs: list[RequiredInput] = []

    # Represents the steps of the scene.
    actionStack: list[ActionStack] = []

    def __str__(self) -> str:
        return f"\nRequiredInputs={self.requiredInputs};\n\nTransformations={self.actionStack};\n"

    def __repr__(self) -> str:
        return str(self)
