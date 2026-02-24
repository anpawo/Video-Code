#!/usr/bin/env python3

from videocode.videocode import *


SOURCE = "test.png"
CELL_SCALE = 0.40

default_input = image(SOURCE).position(x=-800, y=-300).scale(CELL_SCALE)
grayscale_input = image(SOURCE).position(x=0, y=-300).scale(CELL_SCALE).apply(grayscale(), duration=2)
blur_input = image(SOURCE).position(x=800, y=-300).scale(CELL_SCALE).apply(blur(7), duration=2)
gamma_input = image(SOURCE).position(x=-800, y=0).scale(CELL_SCALE).apply(gamma(1.8), duration=2)
grain_input = image(SOURCE).position(x=0, y=0).scale(CELL_SCALE).apply(grain(0.35), duration=2)
brightness_input = image(SOURCE).position(x=800, y=0).scale(CELL_SCALE).apply(brightness(35), duration=2)
contrast_input = image(SOURCE).position(x=-800, y=300).scale(CELL_SCALE).apply(contrast(65), duration=2)
sharpen_input = image(SOURCE).position(x=0, y=300).scale(CELL_SCALE).apply(sharpen(0.8), duration=2)
opacity_sharpen_input = image(SOURCE).position(x=800, y=300).scale(CELL_SCALE).apply(opacity(170), sharpen(0.6), duration=2)
