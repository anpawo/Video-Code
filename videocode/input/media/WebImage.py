#!/usr/bin/env python3


from videocode.input.Input import *


class webImage(Input):
    def __init__(self, url: str) -> None:
        Global.stack.append(
            {
                "action": "Create",
                "type": "WebImage",
                "url": url,
            }
        )
