**Response A:**

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

**Response B:**

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

**Response C:**

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

**Response D:**

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

**Response E:**

Option 3, élargie : le seuil façon Remotion, avec le crédit obligatoire en dessous du seuil et un rachat du crédit au-dessus. C'est la seule des quatre sur laquelle se construit une entreprise.

**« Usage commercial » est invérifiable, un effectif ne l'est pas.** Personne ne signe un accord « à négocier avec l'auteur ». Un juriste d'entreprise qui lit l'option 1 ou 2 referme l'onglet et prend Manim. Un seuil de 3 personnes et un prix affiché passent en note de frais par carte bancaire, sans réunion. Remotion vit de ça.

**Le crédit est l'actif principal, et la question le traite en contrepartie mineure.** « video made with @videocode » sur chaque vidéo YouTube, c'est de la distribution gratuite auprès de la cible exacte, comme le « Sent from my iPhone ». Une chaîne à 500 000 abonnés qui l'affiche vaut plus que n'importe quelle licence d'entreprise la première année. Je le rends donc obligatoire pour tout le palier gratuit. Je le rends retirable dans le palier payant : les agences et les marques paieront uniquement pour ne pas l'afficher.

**Ce que le seuil débloque et qu'un texte maison ferme.**

- **Financement et rachat.** Un investisseur ou un acquéreur audite la propriété intellectuelle en une heure si le modèle est connu, avec un CLA propre et 98,6 % des lignes à un seul auteur. Sur un texte maison en droit français, l'audit dure des semaines.
- **Produit hébergé.** Le moteur C++/Vulkan permet du rendu cloud, une API de génération de vidéos et l'agent IA facturé à l'usage. La clause qui compte interdit de proposer Video-Code en service concurrent. Celle qui vise « le commercial » ne protège pas ce marché.
- **Palier éducation.** C'est le terrain de Manim, et un établissement signe sans discuter.

L'option 4 donne à AWS le droit d'héberger le logiciel. Les options 1 et 2 visent des entreprises qui ne viendront jamais négocier.

À publier avec la licence : une grille de prix, même à 0 client. Le prix affiché fait partie de la licence.
