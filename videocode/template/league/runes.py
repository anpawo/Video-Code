#!/usr/bin/env python3

from __future__ import annotations
from enum import Enum
from videocode.input.group.Incremental import incrAdd, incremental
from videocode.input.media.WebImage import webImage

import requests

from videocode.transformation.setter.SetPosition import setPosition


type Url = str


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


class RuneInput:
    def __init__(self, rune: Rune, url: Url, input: webImage) -> None:
        self.name: Rune = rune
        self.url: Url = url
        self.input: webImage = input


class ShardInput:
    def __init__(self, shard: Shard, url: Url, input: webImage) -> None:
        self.name: Shard = shard
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


class RuneBranch:
    def __init__(self, path: Path, *runes: Rune) -> None:
        self.color = Color[path]
        self.path = UrlKind.get(UrlKind.Icon, path.value)
        self.runes = [RuneInput(rune, u := UrlKind.get(UrlKind.Rune, rune.value), webImage(u)) for rune in runes]
        self.incrementalInputs = incremental({setPosition: incrAdd(y=200)}, *(r.input for r in self.runes))

    def __str__(self) -> str:
        return f"Color:[{self.color}]\nPath:[{self.path}]\nRunes:{self.runes}"


class RuneShard:
    def __init__(self, s1: Shard, s2: Shard, s3: Shard) -> None:
        self.s1 = ShardInput(s1, u := UrlKind.get(UrlKind.Shard, s1.value), ss1 := webImage(u))
        self.s2 = ShardInput(s2, u := UrlKind.get(UrlKind.Shard, s2.value), ss2 := webImage(u))
        self.s3 = ShardInput(s3, u := UrlKind.get(UrlKind.Shard, s3.value), ss3 := webImage(u))
        self.incrementalInputs = incremental({setPosition: incrAdd(y=200)}, ss1, ss2, ss3)


class RuneSet:
    def __init__(
        self,
        *,
        main: tuple[Path, Rune, Rune, Rune, Rune],
        sub: tuple[Path, Rune, Rune],
        shard: tuple[Shard, Shard, Shard],
        animate: bool = True,
    ) -> None:
        self.main = RuneBranch(main[0], *main[1:])
        self.sub = RuneBranch(sub[0], *sub[1:])
        self.shard = RuneShard(*shard)

        self.main.incrementalInputs.setPosition(200, 200)
        self.sub.incrementalInputs.setPosition(600, 200)
        # self.shard.incrementalInputs.setPosition(600, 600)

        # print(self.sub)


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
