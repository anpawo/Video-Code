#!/usr/bin/env python3

from videocode.transformation.Transformation import Transformation

from videocode.Constant import *

class zoom(Transformation):
    """
    `Zoom` `Transformation`.
    """

    def __init__(self, zoomFactor: float = 1.0, zoomCenter: tuple[float, float] = (0.5, 0.5), mode: mode = "static", zoomstart: float = 1.0, zoomend: float = 1.0) -> None:
        """
        :param zoomFactor: zoom factor must be greater than 0, 1.0 = no zoom, 2.0 = 2x zoom
        :param zoomCenter: center of zoom, (0.5, 0.5) = center of the image
        :param mode: static or dynamic
        :param zoomstart: start zoom factor
        :param zoomend: end zoom factor
        """
        if zoomFactor < 1:
            raise ValueError("zoomFactor must be greater than 0")
        self.zoomFactor = zoomFactor
        self.zoomCenter = zoomCenter
        self.mode = mode
        self.zoomstart = zoomstart
        self.zoomend = zoomend

class zoomIn:
    """
    `Zoom in` `Transformation`.
    """

    def __new__(cls, zoomFactor: float = 1.0, zoomCenter: tuple[float, float] = (0.5, 0.5)) -> zoom:
        return zoom(zoomFactor, zoomCenter, "dynamic", zoomstart=1.0, zoomend=zoomFactor)

class zoomOut:
    """
    `Zoom out` `Transformation`.
    """

    def __new__(cls, zoomFactor: float = 1.0, zoomCenter: tuple[float, float] = (0.5, 0.5)) -> zoom:
        return zoom(zoomFactor, zoomCenter, "dynamic", zoomstart=zoomFactor, zoomend=1.0)
