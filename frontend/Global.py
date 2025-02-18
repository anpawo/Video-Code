#!/usr/bin/env python3


type Arguments = list[int | float | str | Arguments]
type RequiredInputs = list[tuple[str, Arguments]]
type TransformationStack = list[tuple[str, int, Arguments]]


class Global:
    """
    Globals used by the classes `Input` and `Transformation`.
    """

    # Input Variables declared in a scene.
    requiredInputs: RequiredInputs = []

    # Represents the steps of the scene.
    transformationStack: TransformationStack = []

    def __str__(self) -> str:
        return f"\nRequiredInputs={self.requiredInputs};\n\nTransformations={self.transformationStack};\n"

    def __repr__(self) -> str:
        return str(self)
