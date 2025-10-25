#!/usr/bin/env python3

from __future__ import annotations
from enum import Enum
from typing import Callable
from videocode.Constant import SH, SINGLE_FRAME, SW, Index, Url
from videocode.input.group.Group import group
from videocode.input.group.Incremental import constantAdd, incremental, linearAdd
from videocode.input.media.WebImage import webImage
from videocode.utils.composition import compose

import requests

from videocode.transformation.Transformation import Transformation
from videocode.transformation.position.MoveTo import moveTo
from videocode.transformation.setter.SetPosition import setPosition
from videocode.utils.easings import Easing


class Path(Enum):
    Precision = "Precision"
    Domination = "Domination"
    Resolve = "Resolve"
    Sorcery = "Sorcery"
    Inspiration = "Inspiration"


class Rune(Enum):
    # Precision
    LethalTempo = "Lethal Tempo"
    Triumph = "Triumph"
    LegendAlacrity = "Legend- Alacrity"
    LastStand = "Last Stand"

    # Resolve
    ShieldBash = "Shield Bash"
    BonePlating = "Bone Plating"


class Shard(Enum):
    AdaptativeForce = "Adaptive_Force"
    AttackSpeed = "Attack_Speed"
    AbilityHaste = "Ability_Haste"
    MovementSpeed = "Movement_Speed"
    HealthScaling = "Health_Scaling"
    Tenacity = "Tenacity_and_Slow_Resist"


class RuneData:
    def __init__(self, elem: Rune | Shard, url: Url, input: webImage) -> None:
        self.name: Rune | Shard = elem
        self.url: Url = url
        self.input: webImage = input


Color: dict[Path, str] = {
    Path.Precision: "Yellow",
    Path.Domination: "Red",
    Path.Resolve: "Green",
    Path.Sorcery: "Blue",
    Path.Inspiration: "Light Blue",
}


class UrlKind(Enum):
    Rune = "File:{name}_rune.png"
    Icon = "File:{name}_icon.png"  # Tree Path
    Shard = "File:Rune_shard_{name}.png"  # Rune Shard

    @staticmethod
    def get(kind: UrlKind, name: str) -> Url:
        endpoint = "https://leagueoflegends.fandom.com/api.php"
        params = {
            "action": "query",
            "format": "json",
            "titles": (fmt := kind.value.format(name=name)),
            "prop": "imageinfo",
            "iiprop": "url",
        }

        response = requests.get(endpoint, params=params)
        data = response.json()

        pages = data.get("query", {}).get("pages", {})
        for page in pages.values():
            if "imageinfo" in page:
                return page["imageinfo"][0]["url"]

        raise ValueError(f"{kind} '{fmt}' not found.")


class Branch:
    def __init__(
        self,
        incr: tuple[Callable[[Transformation, Index], Transformation], ...],
        path: Path | None,
        *elems: Rune | Shard,
    ) -> None:
        self.color = Color[path] if path else None
        self.path = UrlKind.get(UrlKind.Icon, path.value) if path else None
        self.elems = [RuneData(e, u := UrlKind.get(UrlKind.Rune if path else UrlKind.Shard, e.value), webImage(u)) for e in elems]
        self.incrementalInputs = incremental({setPosition: incr}, *(e.input for e in self.elems))

    def __str__(self) -> str:
        return f"Color:[{self.color}]\nPath:[{self.path}]\nElems:{self.elems}"


def linearAfterOneAdd(**kwargs) -> Callable[[Transformation, Index], Transformation]:

    def wrapper(t: Transformation, i: Index) -> Transformation:
        for k, v in kwargs.items():
            t.__setattr__(k, t.__getattribute__(k) + v * i + (v * 0.25 if i else 0))

        return t

    return wrapper


class RuneSet:
    def __init__(
        self,
        *,
        main: tuple[Path, Rune, Rune, Rune, Rune],
        sub: tuple[Path, Rune, Rune],
        shard: tuple[Shard, Shard, Shard],
    ) -> None:
        # Y spacing
        runeSpacing = 180
        shardSpacing = 75

        self.x = SW * 0.3
        self.y = SH * 0.2
        self.duration = 0.4

        xDiffSub = SW * 0.3
        yDiffSub = runeSpacing * 0.4

        xDiffShard = xDiffSub
        yDiffShard = runeSpacing * 2.35

        offscreenStart = 2000

        self.main = Branch((linearAfterOneAdd(y=runeSpacing),), *main)
        self.sub = Branch((linearAdd(y=runeSpacing), constantAdd(x=xDiffSub, y=yDiffSub)), *sub)
        self.shard = Branch((linearAdd(y=shardSpacing), constantAdd(x=xDiffShard, y=yDiffShard)), None, *shard)

        self.all = (
            group(
                self.main.incrementalInputs,
                self.sub.incrementalInputs,
                self.shard.incrementalInputs,
            )
            .setPosition(self.x, self.y + offscreenStart)
            .add()
        )

    def animate(self):
        self.all.slideTo(self.x, self.y, easing=Easing.Out, start=SINGLE_FRAME, duration=0.4).add()


# TODO:
# create a stack that keeps track of the used name
# If you want a thumbnail instead of the original image, use iiurlwidth=100 (or desired width).
# https://static.wikia.nocookie.net/leagueoflegends/images/2/26/Precision_icon.png/revision/latest/scale-to-width-down/52?cb=20170926031126

if __name__ == "__main__":
    r = RuneSet(
        main=(Path.Precision, Rune.LethalTempo, Rune.Triumph, Rune.LegendAlacrity, Rune.LastStand),
        sub=(Path.Resolve, Rune.ShieldBash, Rune.BonePlating),
        shard=(Shard.AdaptativeForce, Shard.AttackSpeed, Shard.HealthScaling),
    )
