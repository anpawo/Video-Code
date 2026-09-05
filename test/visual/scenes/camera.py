#!/usr/bin/env python3

# Visual regression scene — the camera (A2), and what opts out of it.
#
# `camera` moves and zooms the WHOLE picture with one matrix in the vertex
# stage. Sampled at frames 0, 15 and 29 of a one-second pan-and-zoom, so a
# break shows up as an obviously wrong picture rather than a subtle drift:
#
#   frame 0   the world as written — three shapes in a row above a cropped
#             yellow square, and a white caption bar near the bottom.
#   frame 15  half-way: everything is bigger and has slid LEFT, because the
#             camera moved right. The caption has not.
#   frame 29  arrived, at zoom 1.8 looking at x = 1.5.
#
# Three things fail loudly here:
#
#   - the caption bar is pinToFrame()'d, so it is IDENTICAL in all three
#     frames. If it grows or slides, the pin is broken and every subtitle in
#     the library goes with it.
#   - the yellow square is cropped 25% off each side, and a crop resolves its
#     region from the shape's ON-SCREEN box. A camera that moved the geometry
#     but not the box would leave the cut behind, slicing the square somewhere
#     it is not.
#   - the shapes must both move and grow. One without the other is a camera
#     that pans but does not zoom, or zooms about the wrong point.

from videocode import *

BG = rgba(18, 18, 24)

Circle(radius=0.8, fillColor=RED_B, strokeColor=TRANSPARENT).position(-4, 1.4)
Square(side=1.6, fillColor=GREEN_A, strokeColor=TRANSPARENT).position(0, 1.4)
Triangle(fillColor=BLUE_C, strokeColor=TRANSPARENT).position(4, 1.4)

Square(side=1.6, fillColor=YELLOW, strokeColor=TRANSPARENT) \
    .position(0, -0.9) \
    .apply(crop(left=25, right=25), duration=1)

# Frame space: the camera never touches it.
Rectangle(width=7, height=0.7, fillColor=WHITE, strokeColor=TRANSPARENT) \
    .position(0, -4) \
    .pinToFrame()

camera.moveTo(x=1.5, duration=1)
camera.over(duration=1).zoom = 1.8

wait(1)
