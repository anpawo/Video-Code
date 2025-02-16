#!/usr/bin/env python3

from abc import ABC, abstractmethod
from frontend.Global import *


class Scene(ABC):
    """
    Parent class for scenes.

    Needed to filter out classes made by the user for anything else other than a `Scene`.
    """

    @abstractmethod
    def scene(self) -> None: ...
