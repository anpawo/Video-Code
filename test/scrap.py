#!/usr/bin/env python3


import requests


def get_rune_text(name: str) -> str:
    endpoint = "https://leagueoflegends.fandom.com/api.php"
    params = {
        "action": "query",
        "format": "json",
        "titles": f"File:{name}_rune.png",
        "prop": "extracts",
        "explaintext": True,
    }

    response = requests.get(endpoint, params=params)
    data = response.json()

    pages = data.get("query", {}).get("pages", {})
    for page in pages.values():
        if "extract" in page:
            return page["extract"]

    raise ValueError(f"No text found for rune '{name}'.")


print(get_rune_text("Conqueror"))
