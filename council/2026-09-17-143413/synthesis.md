@@AGREES
- **Option 2, trois voix sur cinq.** L'avocat PI, le juriste conformité et le créateur YouTube choisissent PolyForm Noncommercial avec l'exception vidéo. Les cinq relecteurs ont désigné la réponse de l'avocat comme la plus forte, sans savoir de qui elle venait.
- **Le texte maison VCL-1.1 est rejeté par les cinq.** Les scanners le classent « licence inconnue » et les entreprises le refusent d'office (juriste). Un contrat d'adhésion flou se lit contre celui qui l'a écrit, art. 1190 (avocat). Le créateur ne saurait pas l'expliquer à un sponsor. Le mainteneur et le fondateur disent la même chose : le juriste d'en face ferme l'onglet et prend Manim.
- **PolyForm reste intact, l'exception va dans un fichier à part.** L'avocat et le juriste le disent chacun de leur côté ; le mainteneur le dit à l'envers : une ligne ajoutée au texte en refait un texte maison.
- **Le pire état est celui d'aujourd'hui.** Sans fichier de licence, le créateur repart sans installer. Tout est réservé, donc n'importe quel choix est une ouverture et rien n'oblige à attendre (avocat, juriste, créateur).
- **Les 13 PNG de chess.com sortent avant de poser la licence**, pas après (avocat, juriste).
- **« Une vidéo faite pour un client » doit être tranché noir sur blanc** (mainteneur, créateur) : c'est la première question que tout le monde posera.

@@CLASHES
- **Le crédit obligatoire.** Le mainteneur : une clause qu'on ne peut pas faire respecter ne protège rien et fait fuir les gens honnêtes ; mieux vaut un carton de fin activé par défaut. Le fondateur : le crédit est l'actif principal, de la distribution gratuite chez la cible exacte. Le créateur : une ligne en description ne gêne pas, il le fait déjà pour la musique. Les deux côtés se tiennent : le crédit vaut cher, et personne ne peut le faire respecter par la force.
- **AGPL contre non-commercial.** Le mainteneur : sous AGPL le contributeur reçoit quelque chose en échange, et les empaqueteurs acceptent le texte. L'avocat : une vidéo n'étant pas une œuvre dérivée, un prestataire exploite l'AGPL sans rien devoir, et la GPL interdit d'imposer un crédit sur les sorties. L'AGPL sert les contributeurs, le non-commercial sert les objectifs que l'auteur a écrits.
- **Le seuil façon Remotion.** Le fondateur le défend seul. Les cinq relecteurs l'ont désigné comme le plus gros angle mort : pas de société pour facturer, un SaaS de trois personnes qui revend le logiciel ne paie rien, et une grosse chaîne YouTube paie — l'inverse exact des deux objectifs.

@@BLIND
- **Le statut des scènes (5 relecteurs sur 5).** Une scène est du code Python qui importe la bibliothèque. Aucune des quatre options ne dit si un créateur peut publier, partager ou vendre ses scènes et ses templates, ni à qui est le code écrit par l'agent. Manim vit de ce partage. Sous AGPL ces scripts seraient contaminés ; sous PolyForm, vendre un template est un usage commercial.
- **Le nom « videocode » n'est pas déposé (3 sur 5).** Tout le crédit repose dessus. Contre un tiers qui réemballe le logiciel, un dépôt à l'INPI protège mieux qu'une clause, pour bien moins cher qu'un procès.
- **Le sens unique (1 sur 5).** Une licence stricte peut s'assouplir plus tard vers l'AGPL ou le MIT ; l'inverse est impossible. Dans le doute, commencer strict.
- **Le crédit n'a pas de levier YouTube (1 sur 5).** La vidéo n'étant pas une œuvre dérivée, aucun retrait de plateforme n'est possible pour un crédit manquant. Le levier de l'avocat ne vaut que contre qui redistribue ou héberge le logiciel.
- **Vérifié par le président pendant la séance.** Qt et FFmpeg sont liés en statique sur cette machine (`libQt6Core.a`, `libavcodec.a`) : l'alerte du juriste est réelle, et elle ne concerne que le jour où un binaire est distribué. Le dépôt a 1 fork et 4 étoiles : la question du mainteneur a sa réponse, personne n'a rien à réclamer.

@@RECO
Option 2, en variante, et je suis la majorité : `LICENSE` contient PolyForm Noncommercial 1.0.0 sans un mot changé, et un fichier `LICENSE-EXCEPTION.md` ajoute deux permissions. La première est l'exception vidéo créditée, avec le cas « vidéo pour un client » écrit noir sur blanc. La seconde règle l'angle mort des cinq : les scènes, templates et le code écrit par l'agent appartiennent à celui qui les écrit, qui en fait ce qu'il veut. On commence strict parce que c'est le seul sens qui se rattrape. Le CLA s'écrit selon le droit français (droits listés, durée légale, gratuité dite, accord contribution par contribution), et le nom se dépose à l'INPI. Le texte de l'exception et du CLA mérite une heure d'avocat : c'est le seul endroit où une erreur ne se rattrape pas.

@@ONE
Sortir de `HEAD` ce qui n'est pas à toi — les 1 060 lignes des co-auteurs (ligne 59 du tableau) et les 13 PNG de chess.com — puis poser un tag : la licence court à partir de ce tag.
