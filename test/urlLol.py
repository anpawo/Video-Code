import requests


def get_image_url(image_name: str) -> str:
    """
    Given a file name (e.g. 'Lethal_Tempo_rune.png'),
    returns the direct image URL from the League of Legends wiki.
    """
    endpoint = "https://leagueoflegends.fandom.com/api.php"
    params = {
        "action": "query",
        "format": "json",
        "titles": f"File:{image_name}",
        "prop": "imageinfo",
        "iiprop": "url",
    }

    response = requests.get(endpoint, params=params)
    data = response.json()

    pages = data.get("query", {}).get("pages", {})
    for page in pages.values():
        if "imageinfo" in page:
            return page["imageinfo"][0]["url"]

    return "error"


if __name__ == "__main__":
    image_name = "Lethal_Tempo_rune.png"
    image_name = "Conqueror_rune.png"
    url = get_image_url(image_name)
    print(url)
