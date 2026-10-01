# Council: 17 septembre 2026, 14 h 34

## Original question

Quelle licence pour video-code — texte maison VCL-1.1, PolyForm Noncommercial + exception vidéo créditée, seuil façon Remotion, ou double copyleft façon Qt ? (Les ~1 060 lignes des co-auteurs seront supprimées puis réécrites : déjà décidé.)

## Framed question

DÉCISION. Quelle licence publier pour Video-Code, parmi quatre options :
  1. VCL-1.1, texte maison : usage non commercial libre ; tout usage commercial exige un accord négocié avec l'auteur ; exception : publier des vidéos en ligne, même monétisées ou sponsorisées, est permis sans accord si chaque vidéo porte le crédit « video made with @videocode » (à l'écran, ou en description avec lien) ; 30 jours pour réparer un crédit oublié ; licence révocable seulement sur faute non corrigée ; contributions sous CLA façon Qt (le contributeur garde son copyright, donne une licence irrévocable avec droit de relicencier) ; droit français.
  2. PolyForm Noncommercial 1.0.0 (texte standard rédigé par des avocats) + la même exception vidéo créditée greffée dessus.
  3. Seuil façon Remotion : gratuit pour les particuliers et les structures de 3 personnes ou moins, licence payante au-delà, sans notion de « usage commercial ».
  4. Double licence façon Qt : GPL/AGPL gratuite + licence commerciale payante pour qui ne veut pas du copyleft.

LE PRODUIT. Video-Code : logiciel de montage vidéo où la scène s'écrit en Python et se rend par un moteur C++/Vulkan, avec un éditeur Qt/QML (timeline, inspector, agent IA). Concurrents proches : Manim (MIT), Motion Canvas (MIT), Remotion (licence à seuil). Cible : créateurs de vidéos explicatives, YouTube en premier. ~79 000 lignes. Dépôt public sur GitHub depuis 2024, SANS aucun fichier de licence à ce jour. Aucun utilisateur payant, aucun revenu, pas de société : un seul développeur, étudiant, en France.

FAITS.
- Auteur principal : 98,6 % des lignes actuelles. Trois anciens co-auteurs détiennent ~1 060 lignes (surtout de la doc). DÉCISION DÉJÀ PRISE, à ne pas re-débattre : ces lignes seront supprimées puis réécrites ; l'historique git reste tel quel.
- Dépendances : Qt 6 (LGPL-3, modules LGPL seulement), FFmpeg (build LGPL), OpenCV (Apache-2), protobuf/pybind11/glslang (BSD), nlohmann-json/argparse (MIT), FreeType (FTL), curl, miniaudio. Un template d'échecs importe python-chess (GPL-3) : il a été sorti de la licence et donné en MIT-0. Les 13 PNG de pièces d'échecs du dépôt viennent de chess.com et devront être remplacés.
- Une vidéo produite avec le logiciel n'est pas une œuvre dérivée du logiciel : le copyleft ne touche pas les vidéos.
- Objectifs de l'auteur, dans ses mots : rester seul propriétaire ; que n'importe qui puisse l'utiliser gratuitement pour ses vidéos YouTube, monétisées comprises, contre un crédit visible ; que les entreprises qui s'en servent pour gagner de l'argent autrement (SaaS, prestation, produit payant) passent par un accord avec lui ; pouvoir accepter des contributions sans perdre la main.

ENJEU. Une licence se change difficilement une fois des utilisateurs et contributeurs arrivés : les versions déjà publiées restent sous l'ancienne. Trop stricte ou trop étrange, personne n'adopte l'outil face à Manim et Motion Canvas en MIT. Trop lâche, un tiers l'emballe et le revend. Mal rédigée, elle est inapplicable en droit français et l'auteur n'a pas les moyens d'un procès. Dire laquelle des quatre (ou quelle variante) et pourquoi.

## Workspace context used

- Brouillon VCL-1.1 et ses corrections (§2, §3, §5, §7, §12), discutés dans la session.
- `git blame -w -M -C` : 98,6 % des lignes à l'auteur, ~1 060 lignes à trois co-auteurs.
- `vcpkg.json`, `CMakeLists.txt`, `requirements.txt` : dépendances et leurs licences ; `python-chess` en GPL-3, PNG de chess.com.
- Sièges choisis pour le sujet (casting métier) sur le protocole llm-council ; voir le tableau des sièges dans la session.

---

## Round 1: Advisor responses (raw, de-anonymized)

### The Contrarian

*Siège : mainteneur open source sceptique*

**Option 4, en AGPL-3.0 + licence commerciale. Et renoncer au crédit obligatoire.**

Les options 1 et 2 cassent sur la frontière du « commercial » :
- Un freelance qui monte une vidéo sponsorisée pour la chaîne d'un client fait-il une vidéo publiée (permise) ou une prestation (accord requis) ?
- Même question pour un prof sur un MOOC payant, ou une université.
- Chaque cas flou devient un mail à un étudiant seul.
- Dans le doute, le juriste d'en face répond « non, prenez Manim ».
- Greffer une exception sur PolyForm redonne un texte maison : l'avantage « rédigé par des avocats » disparaît dès la première ligne ajoutée.

Le crédit obligatoire ne se fait pas respecter :
- L'auteur ne peut pas auditer YouTube.
- Il n'a pas les moyens d'un procès.
- Une clause jamais appliquée ne protège rien et fait seulement fuir les gens honnêtes.

Le CLA posé sur du non-commercial tue les contributions :
- Le contributeur travaille gratuitement sur un code que seul l'auteur a le droit de vendre.
- Sous AGPL, il reçoit au moins le copyleft en échange : c'est le marché de Qt, et il est connu.
- Un texte non reconnu par l'OSI ferme aussi Homebrew-core et Debian, et oblige les juristes d'entreprise à le relire à la main.

L'option 3 suppose de vérifier des effectifs. Sans société ni facturation, c'est du théâtre.

Le scénario « un tiers l'emballe et le revend » est imaginaire aujourd'hui :
- 79 000 lignes de C++/Vulkan/Qt, zéro utilisateur.
- Le vrai danger est l'obscurité, face à deux concurrents en MIT.
- L'AGPL couvre déjà le seul cas crédible : le SaaS doit publier son code ou négocier, sans qu'il faille définir « commercial ».

Ce que l'auteur perd est le crédit imposé. À la place :
- Un carton de fin activé par défaut, désactivable.
- Une demande polie dans le README.
- Le crédit viendra de l'adoption plus sûrement que d'une clause.

Reste une question non posée : après deux ans de dépôt public sans licence, qui a déjà forké ? Il faut le vérifier avant de publier quoi que ce soit.

### The First Principles Thinker

*Siège : avocat en propriété intellectuelle, droit français*

La question est mal posée. Sans fichier LICENSE, tout est aujourd'hui réservé, donc vous ne serez jamais en position plus forte. Le texte sortant n'est pas non plus l'irréversible. Seul titulaire des droits, vous pouvez relicencier les versions futures quand vous voulez. La vraie question est de savoir quel levier vous avez avec 0 € de budget contentieux. Il y en a deux. Le premier est le retrait de plateforme (GitHub, YouTube). Le second est le réflexe de conformité du juriste d'entreprise. Les deux ne réagissent qu'à un texte reconnu.

**Je choisis l'option 2, en variante.**

- **Texte.** Gardez PolyForm Noncommercial 1.0.0 intact. Placez l'exception vidéo dans un fichier séparé de « permission additionnelle », sur le modèle de la Classpath Exception. Un standard retouché n'est plus un standard.
- **Contre VCL-1.1.** Selon l'art. 1190 du Code civil, le contrat d'adhésion s'interprète contre son rédacteur. Chaque flou sur « usage commercial » jouera donc contre vous. PolyForm prévoit déjà 32 jours pour réparer, ce qui rend vos 30 jours maison inutiles.
- **L'option 4 rate l'objectif.** Les vidéos ne sont pas des œuvres dérivées, donc un SaaS ou un prestataire exploite l'AGPL sans rien vous devoir. La GPL interdit aussi d'imposer un crédit sur les sorties.
- **L'option 3 aussi.** Un auteur seul ne peut pas vérifier le seuil de 3 personnes, et elle ne prévoit aucun crédit.
- **Sanction.** Depuis l'arrêt Cass. 1re civ., 5 oct. 2022 (Entr'ouvert c/ Orange), le dépassement d'une licence de logiciel ouvre l'action en contrefaçon, et pas seulement la responsabilité contractuelle.

**L'irréversible est le CLA.** C'est là que L131-3 s'applique.
- **Droits cédés.** Énumérez reproduction, adaptation, distribution et sous-licence, pour le monde entier.
- **Durée.** Écrivez « durée légale des droits », jamais « perpétuel ». L'art. 1210 rend un engagement perpétuel résiliable à tout moment.
- **Gratuité.** Stipulez-la expressément (L122-7).
- **Portée.** Recueillez le consentement contribution par contribution, jamais pour l'avenir en bloc. L131-1 frappe de nullité la cession globale d'œuvres futures.

**Trois finitions.**
- Faites courir la licence à partir d'un tag. Les commits antérieurs contiennent du code tiers que vous ne pouvez pas licencier.
- Retirez les 13 PNG de chess.com avant de publier la licence.
- Envoyez toute mise en demeure par lettre recommandée électronique, qui coûte quelques euros et donne une date opposable. Joignez une traduction française informative pour les consommateurs.

### The Expansionist

*Siège : fondateur d'un outil dev semi-ouvert*

Option 3, élargie : le seuil façon Remotion, avec le crédit obligatoire en dessous du seuil et un rachat du crédit au-dessus. C'est la seule des quatre sur laquelle se construit une entreprise.

**« Usage commercial » est invérifiable, un effectif ne l'est pas.** Personne ne signe un accord « à négocier avec l'auteur ». Un juriste d'entreprise qui lit l'option 1 ou 2 referme l'onglet et prend Manim. Un seuil de 3 personnes et un prix affiché passent en note de frais par carte bancaire, sans réunion. Remotion vit de ça.

**Le crédit est l'actif principal, et la question le traite en contrepartie mineure.** « video made with @videocode » sur chaque vidéo YouTube, c'est de la distribution gratuite auprès de la cible exacte, comme le « Sent from my iPhone ». Une chaîne à 500 000 abonnés qui l'affiche vaut plus que n'importe quelle licence d'entreprise la première année. Je le rends donc obligatoire pour tout le palier gratuit. Je le rends retirable dans le palier payant : les agences et les marques paieront uniquement pour ne pas l'afficher.

**Ce que le seuil débloque et qu'un texte maison ferme.**

- **Financement et rachat.** Un investisseur ou un acquéreur audite la propriété intellectuelle en une heure si le modèle est connu, avec un CLA propre et 98,6 % des lignes à un seul auteur. Sur un texte maison en droit français, l'audit dure des semaines.
- **Produit hébergé.** Le moteur C++/Vulkan permet du rendu cloud, une API de génération de vidéos et l'agent IA facturé à l'usage. La clause qui compte interdit de proposer Video-Code en service concurrent. Celle qui vise « le commercial » ne protège pas ce marché.
- **Palier éducation.** C'est le terrain de Manim, et un établissement signe sans discuter.

L'option 4 donne à AWS le droit d'héberger le logiciel. Les options 1 et 2 visent des entreprises qui ne viendront jamais négocier.

À publier avec la licence : une grille de prix, même à 0 client. Le prix affiché fait partie de la licence.

### The Outsider

*Siège : créateur YouTube, l'utilisateur visé*

J'arrive sur le dépôt, je cherche « License » dans la colonne de droite de GitHub. Aujourd'hui : rien. Donc je pars. Pas de licence = je n'ai le droit de rien, et j'ai déjà perdu une vidéo sur une réclamation. C'est ça le vrai problème, pas le choix entre quatre textes.

Mon tri en deux minutes :

- **Option 4 (GPL/AGPL)** : « copyleft », « AGPL » — je ne sais pas ce que ça veut dire pour MES vidéos. La phrase « une vidéo n'est pas une œuvre dérivée » est évidente pour l'auteur, invisible pour moi. J'ai peur, je pars chez Manim.
- **Option 3 (seuil 3 personnes)** : je suis seul, puis j'ai un monteur, un miniaturiste, un freelance. Ils comptent ? Ma chaîne grandit et je deviens hors-la-loi sans le savoir. Non.
- **Option 1 (texte maison)** : « révocable », « accord négocié », « droit français », « CLA ». Un texte que personne d'autre n'utilise, écrit par un étudiant : mon sponsor ou mon client demandera « c'est quoi cette licence ? » et je n'aurai pas de réponse.
- **Option 2** : PolyForm a un nom, une page web, je peux envoyer un lien. Je prends celle-là.

Le crédit ne me gêne pas : une ligne en description, je le fais déjà pour la musique. Mais trois trous qui me feraient fuir :

- **Vidéo pour un client** : c'est une « prestation » ou une « vidéo publiée en ligne » ? Les deux. Tranchez-le noir sur blanc.
- **TikTok/Instagram** : pas de description avec lien cliquable. Crédit à l'écran obligatoire sur chaque short ? Dites-le.
- **Sponsor qui refuse un logo tiers à l'image** : la description suffit-elle toujours ?

Et surtout : mettez en haut du README trois lignes en français simple — « YouTube monétisé : oui, gratuit, créditez. Vidéo client : oui/non. Revendre le logiciel : contactez-moi. » Je ne lirai jamais la licence. Je lirai ces trois lignes.

Option 2, avec ce résumé.

### The Executor

*Siège : juriste conformité open source*

Option 2, et elle se pose lundi matin en une demi-journée.

L'option 1 (VCL-1.1) rate sur un point mécanique. Un texte maison donne `NOASSERTION` sur GitHub, « unknown licence » dans FOSSA, Snyk ou ScanCode, donc un refus automatique dans toute structure dotée d'un scanner. Chaque clause inédite en droit français est une clause que vous devrez défendre seul. PolyForm Noncommercial 1.0.0 a un identifiant SPDX officiel (`PolyForm-Noncommercial-1.0.0`), que les outils et les juristes reconnaissent.

Pour greffer l'exception sans casser le texte :
- `LICENSE` contient le texte PolyForm intact, pas un mot changé. Si vous le modifiez, vous perdez le droit au nom.
- `LICENSE-EXCEPTION.md` contient la permission additionnelle (vidéos publiées avec le crédit, délai de 30 jours), rédigée comme une permission en plus et jamais comme une restriction.
- Les en-têtes portent `SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0 WITH LicenseRef-VideoCode-video-exception`.
- PolyForm prévoit déjà 32 jours pour réparer une violation, donc n'ajoutez aucune clause de révocation.
- Le droit français passe par une phrase dans l'exception et dans l'accord commercial, pas par une retouche du texte standard.

Le reste de la journée :
- `THIRD-PARTY-NOTICES.md`, qui liste Qt, FFmpeg, FreeType et les autres.
- `CONTRIBUTING.md` et CLA Assistant, une GitHub App gratuite qui se branche en 20 minutes. Un DCO ne suffit pas, car il ne donne aucun droit de relicencier.

Deux choses vont vraiment prendre du temps.

1. **La LGPL sur les binaires.** Il faut Qt et FFmpeg en liaison dynamique, remplaçables par l'utilisateur. Il faut aussi les textes LGPL-3 et GPL-3 joints, une offre des sources, et aucune clause interdisant la rétro-ingénierie nécessaire au débogage. PolyForm n'en contient pas, un texte maison en contiendrait par accident. Vérifiez que vcpkg ne lie pas Qt en statique sur macOS : c'est le cas à surveiller.
2. **Les 13 PNG de chess.com.** Tant qu'ils sont dans `HEAD`, vous publiez sous votre licence des fichiers qui ne vous appartiennent pas. Remplacez-les avant de poser `LICENSE`, pas après.

L'option 3 demande une grille tarifaire et une société que vous n'avez pas. L'option 4 est la seule alternative propre, mais l'AGPL ne dit rien du crédit vidéo, qui est votre exigence numéro un.

Dernier point : sans fichier de licence depuis 2024, le dépôt est aujourd'hui « tous droits réservés ». N'importe quel choix est une ouverture, et personne ne peut invoquer une version antérieure plus permissive. Vous n'avez donc aucune raison d'attendre.

---

## Anonymization map

Session timestamp: `2026-09-17-143413 (epoch 1789648453)` · permutation index: `13`

| Advisor | Letter shown to reviewers |
|---|---|
| Contrarian | A |
| First Principles Thinker | C |
| Expansionist | E |
| Outsider | B |
| Executor | D |

---

## Round 2: Peer reviews (reviewers saw only the anonymized A to E responses)

### Reviewer 1

**1. Réponse la plus forte : C.**
- C'est la seule qui raisonne à partir du vrai levier d'un auteur sans budget contentieux : le retrait de plateforme et le réflexe de conformité des juristes d'entreprise.
- C'est aussi la seule qui identifie le CLA comme le point irréversible, avec les articles à respecter (L131-1, L131-3, 1210).
- Elle ajoute deux points que les autres n'ont pas : l'arrêt Entr'ouvert c/ Orange, et une licence qui court à partir d'un tag.
- D est son complément opérationnel, avec moins de fond juridique.

**2. Plus gros angle mort : E.**
- E affirme qu'un effectif est vérifiable. Un étudiant seul ne peut rien auditer.
- E construit une grille de prix, un palier payant et un rachat du crédit sans société. Elle ne dit jamais qui facture, sous quel statut, ni avec quelle TVA.
- La contrainte « pas de société, aucun revenu » figurait pourtant dans la question.

**3. Ce que les cinq ont manqué.**
- **Les scènes.** Elles sont du code Python qui importe la bibliothèque. La vidéo n'est pas une œuvre dérivée, mais le script et les templates le sont peut-être. Personne ne dit si un créateur peut publier, partager ou vendre ses scènes et templates. Or c'est ainsi que l'outil peut se diffuser face à Manim.
- **La marque.** Le crédit repose sur « @videocode », un nom ni déposé ni réservé. Contre un tiers qui réemballe le logiciel, un dépôt INPI protège mieux qu'une clause de licence, pour un coût modeste.

### Reviewer 2

1. **C.** C est la seule à dire ce qui est vraiment irréversible : le CLA, pas le texte de licence, puisqu'un titulaire unique peut relicencier les versions futures. Elle donne les articles à respecter (L131-1, L131-3, 1210) et les deux leviers utilisables sans budget : le retrait de plateforme et l'action en contrefaçon. Elle fait aussi partir la licence d'un tag. D est la meilleure sur l'exécution, mais ne justifie pas pourquoi l'option 2 tient juridiquement.

2. **E.** Un seuil payant suppose une entité qui facture, avec TVA, contrat et grille de prix. L'auteur est étudiant, sans société. E déclare aussi un effectif « vérifiable » sans dire comment un auteur seul le vérifierait. Enfin, E contredit l'objectif déclaré : YouTube gratuit quelle que soit la taille de la structure.

3. **Deux manques communs aux cinq réponses.**
- **Le statut des scripts de scène.** La vidéo n'est pas une œuvre dérivée, mais le script Python de l'utilisateur importe la bibliothèque. Aucune option ne dit si l'utilisateur peut le publier, ou vendre des templates. Sous AGPL, ce script est probablement contaminé ; sous PolyForm, vendre un template est un usage commercial.
- **La marque.** Tout repose sur le crédit « @videocode », et ce nom n'est pas déposé. Un fork peut le reprendre. Un dépôt à l'INPI coûte moins cher qu'un procès.

### Reviewer 3

**1. La plus forte : C.**
- C est la seule à traiter l'enjeu « inapplicable en droit français » avec des textes précis : art. 1190, arrêt Entr'ouvert c/ Orange, L131-1 et L131-3.
- Elle repère aussi que l'irréversible est le CLA, pas la licence.
- D la complète bien avec le SPDX et la conformité LGPL, mais D s'occupe de la mise en place, pas du choix entre les quatre options.

**2. Le plus gros angle mort : E.**
- E bâtit un modèle payant (prix affiché, paiement par carte, grille tarifaire) sans voir que l'auteur n'a ni société ni moyen de facturer.
- Son seuil contredit l'objectif central de l'auteur. Un SaaS de deux personnes qui revend Video-Code ne paie rien, alors que c'est exactement le cas qu'il veut faire passer par un accord.

**3. Ce que les cinq ont raté :**
- **L'asymétrie de sens.** Une licence restrictive peut s'assouplir plus tard vers l'AGPL ou le MIT. L'inverse est impossible, car une version publiée en licence ouverte le reste. Dans le doute, mieux vaut donc commencer strict. Aucun advisor ne le dit.
- **Le fait admis « la vidéo n'est pas une œuvre dérivée » est fragile.** Les scènes Python des utilisateurs importent la bibliothèque. Les vidéos peuvent embarquer des templates et des assets livrés avec le logiciel. Aucune des quatre options ne règle le statut de ces scripts, des templates partagés, ni de ce que l'agent IA génère.

### Reviewer 4

1. **Réponse la plus forte : C.**
- Elle est la seule à déplacer l'irréversible au bon endroit : seul titulaire des droits, l'auteur peut relicencier les versions futures, alors que le CLA, lui, ne se rattrape pas.
- Elle donne des règles utilisables pour ce CLA : L131-1, L131-3, « durée légale » et non « perpétuel », consentement contribution par contribution.
- Elle fait partir la licence d'un tag.
- D est meilleure sur l'exécution (SPDX, LGPL), mais C tranche la vraie question.

2. **Plus gros angle mort : E.**
- Un seuil payant suppose une structure capable de facturer et de vérifier des effectifs. L'auteur est étudiant, sans société, et E affirme pourtant qu'un effectif est « vérifiable ».
- Un SaaS de trois personnes qui revend Video-Code tomberait dans le palier gratuit, soit exactement le cas que l'auteur veut soumettre à un accord.

3. **Ce que les cinq ont manqué :**
- Le fait « la vidéo n'est pas une œuvre dérivée » ne couvre pas la **scène Python**, qui importe la bibliothèque `videocode`.
- Aucune réponse ne dit sous quel statut un créateur peut publier ses scènes, templates ou plugins, ni le code produit par l'agent IA.
- Or l'écosystème de Manim vit de ce partage.
- Piste à examiner : l'API Python en permissif, le moteur et l'éditeur en restrictif.
- Second oubli : le crédit « @videocode » repose sur un nom non déposé à l'INPI. Un tiers peut le prendre.

### Reviewer 5

1. **C.** C est la seule réponse à situer l'irréversible au bon endroit : le texte de licence se relicencie, le CLA non. C est aussi la seule à le rédiger selon le droit français (L131-1, L131-3, « durée légale » plutôt que « perpétuel »). C ajoute trois points utiles que les autres n'ont pas ensemble : la licence posée à partir d'un tag, l'exception dans un fichier séparé, l'arrêt Entr'ouvert. D est plus opérationnelle, mais ne dit rien du CLA en droit français.

2. **E.** E oublie que l'auteur est un étudiant sans société. Il ne peut donc ni facturer, ni encaisser par carte, ni gérer la TVA, alors que tout le modèle d'E repose sur un prix affiché. E ne dit pas non plus comment vérifier un effectif, objection que A et C soulèvent. Enfin, un seuil de 3 personnes fait payer une grosse chaîne YouTube, ce qui contredit l'objectif de gratuité pour les vidéos monétisées.

3. **Le statut du code de l'utilisateur et le lien entre la licence et la vidéo.**
- Les scènes et les templates Python importent la bibliothèque. Sous AGPL, ils deviennent des œuvres dérivées, donc soumis au copyleft. Sous PolyForm, un marché de templates payants devient ambigu. Aucune réponse n'en parle.
- La vidéo n'est pas une œuvre dérivée. Le crédit est donc une simple condition contractuelle d'usage. Un retrait YouTube pour crédit manquant est impossible, et le levier proposé par C tombe.
- Seuls les éléments embarqués dans le rendu (polices, templates, assets) relient juridiquement la licence à la vidéo. Leur licence reste à définir.

---

## Chairman synthesis

### Where the council agrees

- **Option 2, trois voix sur cinq.** L'avocat PI, le juriste conformité et le créateur YouTube choisissent PolyForm Noncommercial avec l'exception vidéo. Les cinq relecteurs ont désigné la réponse de l'avocat comme la plus forte, sans savoir de qui elle venait.
- **Le texte maison VCL-1.1 est rejeté par les cinq.** Les scanners le classent « licence inconnue » et les entreprises le refusent d'office (juriste). Un contrat d'adhésion flou se lit contre celui qui l'a écrit, art. 1190 (avocat). Le créateur ne saurait pas l'expliquer à un sponsor. Le mainteneur et le fondateur disent la même chose : le juriste d'en face ferme l'onglet et prend Manim.
- **PolyForm reste intact, l'exception va dans un fichier à part.** L'avocat et le juriste le disent chacun de leur côté ; le mainteneur le dit à l'envers : une ligne ajoutée au texte en refait un texte maison.
- **Le pire état est celui d'aujourd'hui.** Sans fichier de licence, le créateur repart sans installer. Tout est réservé, donc n'importe quel choix est une ouverture et rien n'oblige à attendre (avocat, juriste, créateur).
- **Les 13 PNG de chess.com sortent avant de poser la licence**, pas après (avocat, juriste).
- **« Une vidéo faite pour un client » doit être tranché noir sur blanc** (mainteneur, créateur) : c'est la première question que tout le monde posera.

### Where the council clashes

- **Le crédit obligatoire.** Le mainteneur : une clause qu'on ne peut pas faire respecter ne protège rien et fait fuir les gens honnêtes ; mieux vaut un carton de fin activé par défaut. Le fondateur : le crédit est l'actif principal, de la distribution gratuite chez la cible exacte. Le créateur : une ligne en description ne gêne pas, il le fait déjà pour la musique. Les deux côtés se tiennent : le crédit vaut cher, et personne ne peut le faire respecter par la force.
- **AGPL contre non-commercial.** Le mainteneur : sous AGPL le contributeur reçoit quelque chose en échange, et les empaqueteurs acceptent le texte. L'avocat : une vidéo n'étant pas une œuvre dérivée, un prestataire exploite l'AGPL sans rien devoir, et la GPL interdit d'imposer un crédit sur les sorties. L'AGPL sert les contributeurs, le non-commercial sert les objectifs que l'auteur a écrits.
- **Le seuil façon Remotion.** Le fondateur le défend seul. Les cinq relecteurs l'ont désigné comme le plus gros angle mort : pas de société pour facturer, un SaaS de trois personnes qui revend le logiciel ne paie rien, et une grosse chaîne YouTube paie — l'inverse exact des deux objectifs.

### Blind spots the council caught

- **Le statut des scènes (5 relecteurs sur 5).** Une scène est du code Python qui importe la bibliothèque. Aucune des quatre options ne dit si un créateur peut publier, partager ou vendre ses scènes et ses templates, ni à qui est le code écrit par l'agent. Manim vit de ce partage. Sous AGPL ces scripts seraient contaminés ; sous PolyForm, vendre un template est un usage commercial.
- **Le nom « videocode » n'est pas déposé (3 sur 5).** Tout le crédit repose dessus. Contre un tiers qui réemballe le logiciel, un dépôt à l'INPI protège mieux qu'une clause, pour bien moins cher qu'un procès.
- **Le sens unique (1 sur 5).** Une licence stricte peut s'assouplir plus tard vers l'AGPL ou le MIT ; l'inverse est impossible. Dans le doute, commencer strict.
- **Le crédit n'a pas de levier YouTube (1 sur 5).** La vidéo n'étant pas une œuvre dérivée, aucun retrait de plateforme n'est possible pour un crédit manquant. Le levier de l'avocat ne vaut que contre qui redistribue ou héberge le logiciel.
- **Vérifié par le président pendant la séance.** Qt et FFmpeg sont liés en statique sur cette machine (`libQt6Core.a`, `libavcodec.a`) : l'alerte du juriste est réelle, et elle ne concerne que le jour où un binaire est distribué. Le dépôt a 1 fork et 4 étoiles : la question du mainteneur a sa réponse, personne n'a rien à réclamer.

### The recommendation

Option 2, en variante, et je suis la majorité : `LICENSE` contient PolyForm Noncommercial 1.0.0 sans un mot changé, et un fichier `LICENSE-EXCEPTION.md` ajoute deux permissions. La première est l'exception vidéo créditée, avec le cas « vidéo pour un client » écrit noir sur blanc. La seconde règle l'angle mort des cinq : les scènes, templates et le code écrit par l'agent appartiennent à celui qui les écrit, qui en fait ce qu'il veut. On commence strict parce que c'est le seul sens qui se rattrape. Le CLA s'écrit selon le droit français (droits listés, durée légale, gratuité dite, accord contribution par contribution), et le nom se dépose à l'INPI. Le texte de l'exception et du CLA mérite une heure d'avocat : c'est le seul endroit où une erreur ne se rattrape pas.

### The one thing to do first

Sortir de `HEAD` ce qui n'est pas à toi — les 1 060 lignes des co-auteurs (ligne 59 du tableau) et les 13 PNG de chess.com — puis poser un tag : la licence court à partir de ce tag.
