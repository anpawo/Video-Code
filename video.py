#!/usr/bin/env python3


from videocode.VideoCode import *
from videocode.template.league.runes import *

r = RuneSet(
    main=(
        Path.Precision,
        Rune.LethalTempo,
        Rune.Triumph,
        Rune.LegendAlacrity,
        Rune.LastStand,
    ),
    sub=(
        Path.Resolve,
        Rune.BonePlating,
        Rune.ShieldBash,
    ),
    shard=(
        Shard.AdaptativeForce,
        Shard.AttackSpeed,
        Shard.HealthScaling,
    ),
).animate()
