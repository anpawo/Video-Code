#!/usr/bin/env python3

#
# montage.py — le montage de la PARTIE (bobine 2), banc d'essai.
#
# chess_montage.py nomme les effets un par un ; ici on s'en sert pour de vrai :
# on prend une fenetre de la partie et on pose dessus quelques mouvements de
# camera — poussees, zooms sur un coup, travellings. Rien d'autre pour le
# moment, le but est de voir si le rythme tient.
#
#   # ouvrir dans l'UI :
#   MONTAGE_SOURCE=~/Desktop/Projets/Evolvia/first_test.mov \
#   ./video-code --editor --file montage.py
#
#   # sortir le fichier, a la taille et au fps de la source :
#   MONTAGE_SOURCE=~/Desktop/Projets/Evolvia/first_test.mov \
#   ./video-code --file montage.py --generate /tmp/montage.mp4 \
#                --width 1322 --height 1526 --framerate 60
#
# Dans les deux cas il FAUT exporter PYTHONPATH avant, l'interpreteur embarque
# ignore le PATH :
#   export PYTHONPATH="$PWD/.venv/lib/python3.14/site-packages"
#

import os

from videocode import *
from videocode.template.effect.framing import containSize
from videocode.template.effect.other.camera import punchIn, reframe, snapZoom, travelling, zoomTo
from videocode.template.effect.other.retime import decimate
from videocode.template.input._inputs import *
from videocode.utils.probe import probeVideo

SOURCE = os.path.expanduser(os.environ.get("MONTAGE_SOURCE", "~/Desktop/Projets/Evolvia/first_test.mov"))

START_AT = 118.0        # ou on entre dans la partie, en secondes de source
REEL = 18.0             # duree de la bobine, en secondes de scene
BORDER = 26             # marquise d'enregistrement macOS, en pixels de chaque bord


# --- la source --------------------------------------------------------------
#
# Sonder, tenir dans le cadre et jeter une frame sur deux sont des outils de la
# librairie (probeVideo, containSize, decimate) : ce fichier ne garde que ce qui
# est propre a CETTE partie.

sourceWidth, sourceHeight, sourceFps = probeVideo(SOURCE)

# La marquise macOS est incrustee dans les pixels : on cadre la zone UTILE et
# on met tout le media a l'echelle pour que les bords sortent du cadre. C'est
# la GEOMETRIE qui le fait, pas le shader `crop` — il n'y a qu'un recadrage par
# image et par input, et on garde ce canal libre pour les effets.
usableWidth = sourceWidth - 2 * BORDER
usableHeight = sourceHeight - 2 * BORDER
keep = containSize(usableWidth, usableHeight)
keepWidth, keepHeight = keep.x, keep.y
clipWidth = keepWidth * sourceWidth / usableWidth
clipHeight = keepHeight * sourceHeight / usableHeight

# En "contain", ce qui n'est pas couvert reste transparent : un fond noir plein
# cadre dessous pour que ce soit des BANDES NOIRES et pas un trou.
backdrop = Rectangle(
    width=WORLD_WIDTH, height=WORLD_HEIGHT,
    fillColor=BLACK, strokeColor=TRANSPARENT,
)
backdrop.position(0, 0).zIndex(-1)

sceneFrames = round(REEL * FRAMERATE)
ratio = sourceFps / FRAMERATE          # 2.0 pour une source a 60 fps
firstFrame = int(START_AT * sourceFps)

clip = Video(
    SOURCE,
    startFrame=firstFrame,
    endFrame=firstFrame + round((sceneFrames - 1) * ratio) + 1,
    cuts=decimate(firstFrame, sceneFrames, ratio),
    width=clipWidth,
    height=clipHeight,
)
clip.position(0, 0).zIndex(0)


# --- ou viser ---------------------------------------------------------------
#
# videocode ne connait pas les echecs, et c'est voulu : les effets de camera
# prennent des FRACTIONS de la boite du media. Traduire "d8" en fraction est le
# boulot de CE fichier, pas celui de la librairie.
#
# Mesure faite une fois sur une image de la source (1322x1526) : le plateau va
# de x=24 a x=1304 et de y=124 a y=1400, soit huit cases de 160 px.
BOARD_X, BOARD_Y, SQUARE = 24.0, 124.0, 160.0
FILES = "abcdefgh"


def square(name: str) -> tuple[float, float]:
    """
    Le centre d'une case, en fractions du media — "d8" -> (0.460, 0.134).

    Le plateau est vu du cote des blancs : la rangee 8 est en haut, donc la
    rangee n occupe la ligne (8 - n) en partant du haut.
    """
    file = FILES.index(name[0])
    rank = int(name[1:])
    x = BOARD_X + (file + 0.5) * SQUARE
    y = BOARD_Y + (8 - rank - 0.5) * SQUARE
    return x / sourceWidth, y / sourceHeight


# --- la bobine --------------------------------------------------------------
#
# Les instants sont cales sur de VRAIS coups de la partie, releves sur la
# source (frame ou les deux cases changent), et ramenes a l'horloge du film :
#   film = (source - START_AT). Coups utilises, en secondes de film :
#     2.84  la dame blanche traverse la colonne d et prend en d8
#     5.84  la tour noire reprend en d8
#    14.17  le pion c2 avance en c4
#    16.51  le fou noir sort en c5
#
# Chaque mouvement arrive un poil AVANT son coup, pour que la camera soit deja
# en place quand la piece bouge — l'inverse donne l'impression de courir apres.
d8 = square("d8")
c4 = square("c4")
c5 = square("c5")
a1 = square("a1")
h8 = square("h8")

# (at, effet, faut-il recadrer derriere)
moves = [
    # Une poussee lente d'entree : la camera n'est jamais fixe, meme quand il
    # ne se passe rien encore.
    (0.0, punchIn(zoom=1.12, duration=2.3), True),

    # La prise de dame : un coup sec, donc snapZoom — il monte vite, tient, et
    # revient tout seul (pas de recadrage derriere, il le fait lui-meme).
    (2.5, snapZoom(x=d8[0], y=d8[1], zoom=2.1, hold=0.9, attack=0.12, release=0.4), False),

    # La reprise, sur la meme case : cette fois une arrivee posee, pour la
    # difference de ton entre les deux coups.
    (5.2, zoomTo(x=d8[0], y=d8[1], zoom=1.9, duration=0.9), True),

    # Le grand balayage du plateau, coin a coin, pendant qu'il ne se passe
    # rien de decisif : ca occupe le temps mort sans le montrer.
    (7.4, travelling(fromX=a1[0], fromY=a1[1], toX=h8[0], toY=h8[1],
                     zoom=1.5, duration=4.2), True),

    # Respiration : on revient large et on repousse doucement.
    (12.0, punchIn(zoom=1.1, duration=1.8), True),

    # Le pion c2-c4.
    (14.0, zoomTo(x=c4[0], y=c4[1], zoom=2.0, duration=0.8), True),

    # Le fou qui sort en c5 : un petit deplacement de camera d'une case a
    # l'autre plutot qu'une coupe.
    (16.0, travelling(fromX=c4[0], fromY=c4[1], toX=c5[0], toY=c5[1],
                      zoom=1.8, duration=1.4), True),
]

# Les `at=` doivent etre croissants : l'horloge du film refuse d'ecrire dans le
# passe d'un element. La liste ci-dessus est deja dans l'ordre, et chaque
# recadrage se glisse juste avant le mouvement suivant.
for index, (at, effect, needsReframe) in enumerate(moves):
    clip.apply(effect, at=at)
    if needsReframe:
        nextAt = moves[index + 1][0] if index + 1 < len(moves) else REEL - 0.2
        clip.apply(reframe(), at=nextAt - 0.15)
