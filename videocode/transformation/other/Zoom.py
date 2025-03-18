#!/usr/bin/env python3

from videocode.transformation.Transformation import Transformation


class zoom(Transformation):
    """
    `Zoom` `Transformation`.

    by default zoom on center
    """

    def __init__(self, zoomFactor: float = 1.0, zoomCenter: tuple[float, float] = (0.5, 0.5)) -> None:
        """
        :param zoomFactor: zoom factor, 1.0 = no zoom, 2.0 = double size
        :param zoomCenter: center of zoom, (0.5, 0.5) = center of the image
        """
        if zoomFactor < 1:
            raise ValueError("zoomFactor must be greater than 0")
        self.zoomFactor = zoomFactor
        self.zoomCenter = zoomCenter
