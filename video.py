#!/usr/bin/env python3


from videocode.VideoCode import *
from videocode.template.league.runes import *

automaticAdderOn()

x = 0.5
y = 0.5

r = RuneSet(
    main=(Path.Precision, Rune.LethalTempo, Rune.Triumph, Rune.LegendAlacrity, Rune.LastStand),
    sub=(Path.Resolve, Rune.ShieldBash, Rune.BonePlating),
    shard=(Shard.AdaptativeForce, Shard.AttackSpeed, Shard.HealthScaling),
)  # .animate()


automaticAdderOff()
