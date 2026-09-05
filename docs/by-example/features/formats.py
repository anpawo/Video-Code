#!/usr/bin/env python3

"""
C3 — une scène, tous les formats : `--for youtube,tiktok,square`.

    ./video-code --file docs/by-example/features/formats.py --generate formats.mp4 \
        --for youtube,tiktok,square

Trois fichiers d'une seule commande — `formats-youtube.mp4` (1920×1080),
`formats-tiktok.mp4` (1080×1920), `formats-square.mp4` (1080×1080).

Ce n'est PAS un recadrage : la scène est rejouée pour chaque forme, et elle se
remet en page. Le `SplitView` ci-dessous résout `Split.AUTO` en colonnes dans
un cadre large et en rangées dans un cadre haut — mesuré, le marqueur est à
0,26 en travers en 16:9 et à 0,26 en hauteur en 9:16.
"""

from videocode import *
from videocode.template.input.SplitView import SplitView

vue = SplitView(ratio=1)
Text(text="A", fontSize=1.4, fillColor=WHITE).position(vue.a.x, vue.a.y)
Text(text="B", fontSize=1.4, fillColor=BLUE_C).position(vue.b.x, vue.b.y)
wait(2)
