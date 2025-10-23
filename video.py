#!/usr/bin/env python3


from videocode.VideoCode import *
from videocode.template.league.runes import *
from videocode.template.movement.slideTo import slideTo

automaticAdderOn()

x = 0.2 * SW
y = 0.2 * SH

# r = RuneSet(
#     main=(Path.Precision, Rune.LethalTempo, Rune.Triumph, Rune.LegendAlacrity, Rune.LastStand),
#     sub=(Path.Resolve, Rune.BonePlating, Rune.ShieldBash),
#     shard=(Shard.AdaptativeForce, Shard.AttackSpeed, Shard.HealthScaling),
# )  # .animate()

c = circle().setPosition(x, y)

slideTo(c, x + 800, y, easing=Easing.Out, duration=1)


automaticAdderOff()
