#!/usr/bin/env python3

"""
A6 — le volume est une revendication, et `duck` écrit le geste du voice-over.

    ./video-code --file docs/by-example/features/sound.py --generate sound.mp4
    (à écouter, pas à regarder)

`music.over(duration=1.5).volume = 0` s'écrivait déjà comme n'importe quelle
autre propriété, et le montage jetait la revendication : le fondu sortait à
plein volume, sans un mot. Le graphe audio lit maintenant le niveau image par
image.

`music.duck(under=voice)` écrit les deux rampes du geste que fait toute vidéo
avec une voix sur de la musique : descente à l'entrée de la voix, remontée à sa
fin. Ce sont des revendications ordinaires, visibles et modifiables.
"""

from videocode import *

Text(text="A6  ·  le son suit ce que la scène revendique", fontSize=0.34, fillColor=WHITE).position(0, 2.6)
Text(text="la musique baisse pendant la voix, puis remonte", fontSize=0.28, fillColor=BLUE_C).position(0, 1.6)

barre = Rectangle(width=0.6, height=0.6, fillColor=GREEN_A, strokeColor=TRANSPARENT)
barre.position(-3, -0.5)
barre.moveTo(x=3, duration=3.4, easing=Easing.Linear)

music = Sound("test/test.wav")
voice = Sound("test/test_speech.wav", start=0.7, trimEnd=1.0)
music.duck(under=voice, to=0.18, fade=0.25)
wait(3.6)
