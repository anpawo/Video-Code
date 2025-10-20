#!/usr/bin/env python3


import requests

from enum import Enum
from videocode.input.media.WebImage import webImage


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


class RuneInput:
    def __init__(self, rune: Rune, url: Url, input: webImage) -> None:
        self.name: Rune = rune
        self.url: Url = url
        self.input: webImage = input


Color: dict[Path, str] = {
    Path.Precision: "Yellow",
    Path.Domination: "Red",
    Path.Resolve: "Green",
    Path.Sorcery: "Blue",
    Path.Inspiration: "Light Blue",
}


class RuneBranch:
    def __init__(self, path: Path, *runes: Rune) -> None:
        self.color = Color[path]
        self.path = self.getIconUrl(path)
        self.runes = [RuneInput(rune, u := self.getRuneUrl(rune.value), webImage(u)) for rune in runes]

    def __str__(self) -> str:
        return f"Color:[{self.color}]\nPath:[{self.path}]\nRunes:{self.runes}"

    def getRuneUrl(self, runeName: str) -> str:
        endpoint = "https://leagueoflegends.fandom.com/api.php"
        params = {
            "action": "query",
            "format": "json",
            "titles": f"File:{runeName}_rune.png",
            "prop": "imageinfo",
            "iiprop": "url",
        }

        response = requests.get(endpoint, params=params)
        data = response.json()

        pages = data.get("query", {}).get("pages", {})
        for page in pages.values():
            if "imageinfo" in page:
                return page["imageinfo"][0]["url"]

        raise ValueError(f"Rune '{runeName}' not found.")

    def getIconUrl(self, treeName: Path) -> str:
        endpoint = "https://leagueoflegends.fandom.com/api.php"
        params = {
            "action": "query",
            "format": "json",
            "titles": f"File:{treeName}_icon.png",
            "prop": "imageinfo",
            "iiprop": "url",
        }

        response = requests.get(endpoint, params=params)
        data = response.json()

        pages = data.get("query", {}).get("pages", {})
        for page in pages.values():
            if "imageinfo" in page:
                return page["imageinfo"][0]["url"]

        raise ValueError(f"Tree '{treeName}' not found.")


class Shard(Enum):
    AdaptativeForce = "Adaptive_Force"
    AttackSpeed = "Attack_Speed"
    AbilityHaste = "Ability_Haste"
    MovementSpeed = "Movement_Speed"
    HealthScaling = "Health_Scaling"
    Tenacity = "Tenacity_and_Slow_Resist"


class ShardInput:
    def __init__(self, shard: Shard, url: Url, input: webImage) -> None:
        self.name: Shard = shard
        self.url: Url = url
        self.input: webImage = input


class RuneShard:
    def __init__(self, s1: Shard, s2: Shard, s3: Shard) -> None:
        self.s1 = ShardInput(s1, u := self.getShardUrl(s1.value), webImage(u))
        self.s2 = ShardInput(s2, u := self.getShardUrl(s2.value), webImage(u))
        self.s3 = ShardInput(s3, u := self.getShardUrl(s3.value), webImage(u))

    def getShardUrl(self, shardName: str) -> str:
        endpoint = "https://leagueoflegends.fandom.com/api.php"
        params = {
            "action": "query",
            "format": "json",
            "titles": f"Rune_shard_{shardName}.png",
            "prop": "imageinfo",
            "iiprop": "url",
        }

        response = requests.get(endpoint, params=params)
        data = response.json()

        pages = data.get("query", {}).get("pages", {})
        for page in pages.values():
            if "imageinfo" in page:
                return page["imageinfo"][0]["url"]

        raise ValueError(f"Rune Shard '{shardName}' not found.")

    # src="https://static.wikia.nocookie.net/leagueoflegends/images/a/a3/Rune_shard_Adaptive_Force.png/revision/latest/scale-to-width-down/30?cb=20181122101607"


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
