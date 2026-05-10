#!/usr/bin/env python3


from videocode import *


class ParticlesRay(Group):
    def __init__(
        self,
        size: number = 0.1,
        nbr: number = 9,
    ) -> None:

        self.size = size
        self.nbr = nbr

        def particles(d: degree):
            c = math.cos(math.radians(d))
            s = math.sin(math.radians(d))
            ln = HorizontalLine(length=size, fillColor=WHITE, strokeColor=TRANSPARENT, rounded=True).rotation(-d)

            return c, s, ln

        self.particles = [particles(deg) for deg in floatRange(0, 360, 360 / nbr)]

        super().__init__(
            *map(lambda p: p[2], self.particles),
        )
        self.hide()

    def animate(self) -> Self:

        def animation(t: tuple[float, float, HorizontalLine]):
            c, s, ln = t

            ln.show().align(x=1).position(
                x=ln.meta.position.x - c * self.size * 0.5,
                y=ln.meta.position.y - s * self.size * 0.5,
            )
            ln.length *= 0.05
            ln.ease(ln.ref.length, self.size, easing=Easing.InOut, duration=0.15).flush()
            ln.align(x=0).position(
                x=ln.meta.position.x - c * self.size,
                y=ln.meta.position.y - s * self.size,
            ).flush()
            ln.ease(ln.ref.length, 0, easing=Easing.In, duration=0.15).flush()

        for particle in self.particles:
            animation(particle)

        return self.hide().flush()
