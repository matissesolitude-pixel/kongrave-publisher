# DOCTRINE CONTENU — PROP FIRM

Le moteur éditorial de la prop firm, transposé de LA LIGNE.
Objectifs des posts : **awareness · education · authority**.
Ratio de publication : **3 reels pour 1 carrousel**.

> `[FIRM]` = le nom de marque, à substituer partout par le PO.
> Tout ce qui est marqué **[PO]** est une décision ou un fait à confirmer
> avant production — aucun chiffre de règle, de split ou de payout n'est
> inventé dans ce document.

---

## 0. CE QU'ON REPREND, CE QU'ON CHANGE

**On reprend de LA LIGNE (la méthode, elle est payée) :**
- Le buster de croyance : une croyance répandue démontée, le vrai mécanisme
  révélé. C'est LA mécanique du format, et elle est encore plus juste ici :
  le produit d'une prop firm EST un jeu de règles mal comprises.
- Le test des 8 ans : sujet adulte, technique, vrais termes — mais clarté
  telle que personne ne décroche.
- Le muet au-dessus de tout : compréhensible son coupé, sans sous-titres.
- L'émotion dès la frame 0, le payoff à 3 secondes, la fin actionnable.
- La file de publication (dépôt → cron → publié), les garde-fous cadence.

**On change :**
- **Le compte.** Contenu prop firm = compte [FIRM], jamais @kongrave_.
  Deux marques, deux audiences, deux promesses.
- **Le poids du carrousel.** LA LIGNE = 1 carrousel pour 5 reels. Ici
  1 pour 3. Le carrousel n'est plus un accompagnement, c'est la moitié
  du travail éditorial (voir §4 et §6).
- **Le sujet.** LA LIGNE explique le marché. [FIRM] explique le marché
  **et son propre produit**. C'est le virage : personne ne le fait.
- **Les briques visuelles.** La grammaire (trait, encre, papier, muet,
  physique calculée) se transfère ; la palette et les objets de LA LIGNE
  ne se copient PAS — deux comptes interchangeables tuent les deux
  marques. **[PO]** : trancher la palette [FIRM] (recommandation : même
  grammaire, accent couleur distinct, pour lire "même famille" sans
  lire "même compte").

---

## 1. LE POSITIONNEMENT — LE SEUL ANGLE DÉFENDABLE

Le marché des prop firms est saturé de deux contenus : la preuve de
payout et le meme. Les deux sont copiables en une journée par n'importe
quel concurrent avec un budget ads (l'annonce PropAccount reçue en
référence est exactement ça : une ad payée, un code affilié, zéro
substance).

Ce qui n'est pas copiable : **être la firme qui explique ses propres
règles.** Le trader ne rate pas son challenge sur le marché — il le rate
sur une règle qu'il n'a pas lue, ou qu'il a lue de travers. La firme qui
décode ces règles devient la firme en qui on a confiance, et la confiance
est la seule monnaie rare d'une catégorie où les traders ont vu des
enseignes fermer et des payouts refusés.

**La ligne éditoriale tient en une phrase :**
> On vous montre exactement comment on gagne de l'argent, et exactement
> comment vous perdez le vôtre.

Conséquence assumée : un contenu qui fait passer plus de traders. C'est
voulu. Une firme dont les traders survivent a un coût d'acquisition qui
s'effondre et une réputation qu'aucune ad ne rachète.

---

## 2. LES TROIS OBJECTIFS — DÉFINITION OPÉRATIONNELLE

**Un post = UN objectif dominant.** Jamais deux. Un post qui essaie de
faire les trois ne fait rien.

### AWARENESS — être vu par ceux qui ne nous suivent pas
- **Cible** : le trader qui n'a jamais entendu parler de [FIRM].
- **Matière** : l'émotion du parcours — le challenge raté à 0,3% du but,
  le compte funded vidé en trois jours, le reset qu'on repaie.
  Reconnaissance de soi ("c'est moi, ça"), injustice, tension.
- **Zéro jargon.** Aucun sigle non expliqué dans les 3 premières secondes.
- **Interdit** : parler de [FIRM]. Un post awareness qui vend est un post
  awareness raté.
- **KPI** : reach non-abonnés, watch time, partages.

### EDUCATION — être gardé
- **Cible** : le trader qui compare des firmes et ne comprend pas les règles.
- **Matière** : le mécanisme. Drawdown trailing vs statique, equity vs
  balance, l'heure de reset de la perte journalière, la règle de
  consistance, le hedging inter-comptes, la fenêtre news, le calendrier
  de payout.
- **Fin actionnable obligatoire** : une règle mémorisable, un critère, un
  calcul à faire avant la session. C'est ce qui déclenche le save.
- **KPI** : saves (le KPI n°1 du carrousel), envois en DM.

### AUTHORITY — être cru
- **Cible** : le trader prêt à payer, qui cherche une raison de ne pas
  se faire avoir.
- **Matière** : la transparence sur [FIRM] — comment la firme gagne de
  l'argent, pourquoi telle règle existe, ce que voit le risk desk, ce qui
  se passe quand un payout est demandé, qui est derrière.
- **Règle absolue** : aucune affirmation factuelle sur [FIRM] qui n'ait
  été confirmée **[PO]**. Un chiffre faux ici détruit tout le reste.
- **KPI** : visites de profil, clics lien, DM entrants qualifiés.

**Répartition cible sur 12 posts** : awareness 4-5 · education 4-5 ·
authority 3. L'awareness et l'éducation portent le volume, l'autorité
porte la conversion.

---

## 3. LA CADENCE — 3 REELS POUR 1 CARROUSEL

**Cycle atomique = 4 posts** : 1 carrousel + 3 reels.
**Rotation = 3 cycles = 12 posts**, l'unité sur laquelle on équilibre les
trois objectifs et on juge la performance.

### La grille (le détail qui compte)
La grille Instagram fait 3 colonnes. Un carrousel tous les 6 posts tient
une **colonne** (6 est multiple de 3) — c'est la règle actuelle de
@kongrave_, écrite en dur dans `publish_carrousel.py` (`MIN_SPACING = 5`).

Un carrousel tous les 4 posts ne peut pas tenir une colonne : il se
décale d'une case à chaque cycle et dessine une **diagonale**, qui boucle
tous les 12 posts.

**Décision recommandée** : garder la diagonale. Elle est régulière,
lisible, et elle vaut mieux que de sacrifier le ratio éditorial à une
géométrie. Si le PO veut une colonne, la seule alternative propre est
1 carrousel pour 2 reels (cycle de 3, 33% de carrousels) — plus de
carrousels, pas moins.

### Rythme de publication
- **1 post/jour**, comme LA LIGNE. Un cycle = 4 jours, une rotation =
  12 jours.
- **Alternance thématique obligatoire** (loi héritée) : on ne publie
  jamais deux posts du même objectif à la suite, ni deux fois le même
  sujet dans une rotation. Ordre par cycle : **carrousel → reel →
  reel → reel**, objectifs brassés (voir `ROTATION_01.md`).

---

## 4. LE PARTAGE DES RÔLES REEL / CARROUSEL

Ce ne sont pas deux emballages du même contenu. Ils font deux métiers.

| | REEL | CARROUSEL |
|---|---|---|
| Ce qu'il achète | de l'**attention** (reach froid) | de la **confiance** (save, relecture) |
| Objectif dominant | awareness | education / authority |
| Unité | une seule idée, une seule image forte | une progression en étapes |
| Ce qu'on y met | l'émotion, le choc, le paradoxe | le mécanisme, le tableau, la checklist |
| KPI | watch time, partages | **saves**, temps par slide |
| Coût de prod | élevé (animation) | faible (slides) |
| Durée de vie | quelques jours | des mois (le save le rappelle) |

**Le sujet qui demande un tableau, une liste ou une comparaison de plus
de deux colonnes est TOUJOURS un carrousel.** Le sujet qui demande une
mise en mouvement (une ligne qui bouge, un compte qui se vide, une masse
qui écrase) est TOUJOURS un reel. Le format suit le sujet, jamais le
planning.

---

## 5. LES LOIS DU CARROUSEL (nouvelles — LA LIGNE ne les avait pas)

Un carrousel n'est pas un reel en tranches. Neuf lois.

**C1 — LA SLIDE 1 EST LE POST.** 90% des gens ne verront qu'elle. Elle
porte une affirmation complète + une tension visible. **≤ 7 mots**,
lisibles en vignette (test : réduire à 150px de large, ça se lit encore).
Jamais "swipe →" comme seul contenu.

**C2 — LA DETTE DU SWIPE.** La slide 1 crée un manque ; la slide 2 en
paie une partie **immédiatement**. Pas de préambule, pas de "avant de
commencer", pas de sommaire. Si la slide 2 n'apprend rien, le carrousel
est mort là.

**C3 — UNE IDÉE PAR SLIDE, UN VISUEL PAR SLIDE.** Pas de paragraphe.
Titre court + **≤ 20 mots** de corps. Si ça ne tient pas, c'est deux
slides.

**C4 — UN PAS NEUF PAR SLIDE** (test de la démangeaison, hérité). On
coupe après chaque slide : reste-t-il une raison contenue de swiper ?
Une slide qui reformule la précédente se supprime.

**C5 — LA SLIDE N-1 EST LA PRISE.** L'avant-dernière slide contient la
chose qu'on veut garder : le calcul, le critère, la règle, le tableau
récapitulatif. C'est elle qui déclenche le save, et le save est le seul
signal de qualité que l'algorithme lit vraiment.

**C6 — LA DERNIÈRE SLIDE EST LE CTA, ET RIEN D'AUTRE.** Le mot-clé DM,
gros, seul. Pas de contenu utile en slide N — on ne cache jamais la
valeur derrière le CTA.

**C7 — LE MUET INTÉGRAL.** Un carrousel n'a pas de son du tout.
L'enchaînement des slides doit raconter l'histoire complète en lisant
uniquement les titres. Test : lire les 8 titres à la suite — c'est une
histoire, ou c'est une liste morte.

**C8 — LA CONTRAINTE TECHNIQUE** (imposée par `publish_carrousel.py` et
l'API Meta) : **JPEG uniquement** (le PNG est refusé), **2 à 10 slides**,
**1080×1350 (4:5)**. Standard [FIRM] : **8 slides**, comme la série C.

**C9 — LA CONTINUITÉ VISUELLE.** Un élément traverse tout le carrousel
(une ligne, une jauge, un compteur) et se transforme de la slide 1 à la
slide N-1. C'est le fusil de Tchekhov du format statique : il donne au
swipe une raison mécanique de continuer.

---

## 6. LES LOIS HÉRITÉES DE LA LIGNE (appliquées telles quelles)

Elles valent pour les reels ET, quand elles ont du sens, pour les
carrousels. Le détail est dans la skill `ligne-moteur` — voici ce qui
s'applique sans discussion :

- **LOI 0 — le copy d'abord.** Aucune image avant que le texte passe le
  test de la démangeaison.
- **LOI 1 — le niveau des 8 ans.** Sujet adulte, clarté totale.
- **LOI 1bis — le hook.** Payoff à 3 secondes · framing négatif ou
  contre-intuitif · curiosity gap · **émotion dès la frame 0** (choc,
  curiosité, injustice, tension, reconnaissance de soi) · fin actionnable.
  Le **buster compressé** ("You think X. It's not. [vrai mécanisme]") est
  la forme par défaut ici — le sujet s'y prête plus encore qu'à LA LIGNE.
- **LOI 2 — le muet au-dessus de tout.**
- **LOI 3 — la physique calculée**, jamais keyframée.
- **LOI 4 — le rythme** : mouvement 80% du temps, aucun geste étiré.
- **LOI 5 — le gabarit 5 séquences** (ouverture / constat / retournement /
  escalade / leçon), 45-90s, décor permanent interdit.
- **LOI 6 — le brief 7 blocs** pour Code (échelle, caméra, couleur,
  rythme, copy figé, interdits, DoD muet).
- **LOI 7 — maquette d'abord, frames avant vidéo.**
- **Une mécanique visuelle distincte par scène.** Jamais le même verbe
  décliné cinq fois.

**Ce qui ne se transfère PAS :** la boule teal, le fusil visuel de
LA LIGNE, la signature "THE LINE — …", les mots-clés LINE/MAP/PROFILE,
et le catalogue brûlé de `MOTEUR_LIGNE.md` §M14 (il est brûlé pour
KONGRAVE, pas pour [FIRM] — mais réutiliser une brique reconnaissable
de LA LIGNE trahit les deux comptes).

---

## 7. LE SYSTÈME DE CTA — TROIS MOTS-CLÉS, PAS QUATRE

Même mécanique que LA LIGNE : un mot-clé en commentaire/DM déclenche
l'envoi automatique du lead magnet (ManyChat), et alimente le workflow
setter.

| Mot-clé | Lead magnet | Posts qui l'utilisent |
|---|---|---|
| **RULES** | Le règlement décodé — une page par règle : ce qu'elle mesure vraiment, quand elle se déclenche, comment on la rate | education |
| **LIMIT** | Le simulateur de drawdown — on entre son solde, on voit où la ligne se trouve aujourd'hui et où elle sera demain | education technique / awareness sur le drawdown |
| **PLAN** | Le plan de pré-challenge — sizing, stop journalier, session, la checklist qui évite de rater sur une règle | awareness → conversion |

Les posts **authority** ne portent pas de lead magnet : leur CTA est le
profil ou l'offre, sobrement. Vendre après avoir prouvé, pas pendant.

**Structure de caption (moule LIGNE, vérifié en vrai) :**
1. **Ligne 1 = le CTA EN PREMIER, avant l'accroche.** Instagram tronque ;
   le mot-clé doit être visible sans déplier "… plus".
   Modèle : `Comment "RULES" [bénéfice ultra-court]. [accroche complète].`
2. Corps : 2-3 phrases qui résument la valeur, registre sec.
3. Signature : une variante de la signature [FIRM] **[PO]** (l'équivalent
   du "THE LINE — …", à créer, à ne pas emprunter).
4. ~10 hashtags : génériques + spécifiques au sujet.

**Premier commentaire épinglé** (double filet) : une accroche liée au
post + le mot-clé, systématiquement. Il déclenche ManyChat même sans
lecture de la caption, et il amorce la section commentaires.

---

## 8. LES GARDE-FOUS — NON NÉGOCIABLES

Une prop firm est plus exposée qu'un compte d'éducation. Ces règles
priment sur toute considération de performance.

**Doctrine héritée :**
- Jamais d'intention prêtée aux institutionnels.
- Jamais "perdre plus que son dépôt".
- Jamais une méthode de chasse aux stops. On enseigne la mécanique et
  l'auto-diagnostic.
- Les concepts de cadre (FVG, OB…) : "the frame calls it", jamais un fait.

**Spécifique prop firm :**
- **Aucune promesse de gain, aucun claim de revenu**, ni en image, ni en
  voix, ni en caption. Pas de "devenez funded", pas de montant projeté.
- **Aucune capture de payout comme appât.** Une preuve de payout n'existe
  que dans un post authority, contextualisée, avec le mécanisme expliqué
  — et validée **[PO]**.
- **Dire ce que l'environnement est vraiment** (simulé / démo / capital
  réel) partout où la question se pose. **[PO]** : arrêter la formulation
  exacte une fois pour toutes, elle sera reprise à l'identique dans tous
  les posts.
- **Jamais un concurrent nommé.** On attaque un mécanisme, jamais une
  enseigne. Un post qui tape sur une marque nous met au même niveau
  qu'elle et nous expose.
- **Jamais expliquer comment contourner une règle** — la nôtre ou celle
  d'un autre. On explique comment une règle fonctionne, pas comment la
  jouer.
- **Ce n'est pas du conseil en investissement.** Aucun signal, aucune
  paire, aucune direction jouable.
- **Politique pub Meta** : pas de langage guru, pas de promesse de
  résultat. La réfutation, pas la promesse. (Un compte qui poste des
  promesses de gain se ferme aussi.)

**Le test avant toute publication** : *"un coach trading high-ticket
retail pourrait-il écrire exactement ça ?"* Si oui → on réécrit.

---

## 9. LE PIPELINE — COMMENT ÇA SE PUBLIE

Le repo publie déjà des reels et des carrousels sur @kongrave_ ; le
contenu [FIRM] réutilise la même mécanique sur un **autre compte**.

**Ce qui existe et se réutilise tel quel :**
- `publish_carrousel.py` — file `carrousel/queue/` → conteneurs image →
  conteneur carrousel → publish → commentaire CTA. Contraintes JPEG /
  2-10 slides / 4:5 déjà appliquées.
- `publish_ligne.py` + `ligne/queue/` — un dossier = un `.mp4` +
  `caption.txt`, le plus ancien part en premier.
- Les garde-fous cadence et espacement, le journal, les notifications.

**Ce qu'il faut instancier pour [FIRM] — [PO], à faire avant le premier
post :**
1. Un **jeu de secrets Meta distinct** (compte [FIRM]) — variables
   d'environnement séparées, pas de partage de token avec @kongrave_.
2. Des **files séparées** : `propfirm/queue_reels/` et
   `propfirm/queue_carrousels/`. On ne mélange pas deux marques dans une
   même file, le risque de publier au mauvais endroit est trop grand.
3. **`MIN_SPACING = 3`** pour la file carrousel [FIRM] (3 reels entre deux
   carrousels), contre 5 pour @kongrave_.

**Je n'ai touché à aucun script existant** : changer `MIN_SPACING` dans
`publish_carrousel.py` modifierait la grille de @kongrave_. Le paramètre
doit devenir une **config par compte** au moment où la file [FIRM] est
créée, pas avant.

**Le manifeste carrousel** (format existant, inchangé) :
```json
{
  "id": "P-C01",
  "slides": [1, 2, 3, 4, 5, 6, 7, 8],
  "caption": "Comment \"RULES\" …",
  "pinned_comment": "… Comment \"RULES\" … 👊"
}
```

---

## 10. LA BOUCLE D'APPRENTISSAGE

On juge par **rotation de 12 posts**, jamais post par post.

| Format | Signal qui décide | Ce qu'on change s'il est mauvais |
|---|---|---|
| Reel awareness | % non-abonnés, skip < 3s | la **frame 0** et la première phrase, rien d'autre |
| Reel education | watch through, saves | le copy (on resserre), pas l'animation |
| Carrousel | **saves**, drop entre slide 1 et 2 | slide 1 (loi C1) ou dette du swipe (C2) |
| Authority | visites de profil, DM entrants | la preuve : trop vague, ou pas assez concrète |

**Une variable changée à la fois.** Le narratif de LA LIGNE a été prouvé
comme ça : on ne modifie que `voice[0]`, le reste intact. Deux changements
simultanés = zéro apprentissage.

**Le juge reste la rétention réelle Instagram**, pas le score d'un outil
de veille. Format Finder sert à étudier des patterns, jamais à valider un
post.

---

## 11. CE QUI RESTE À TRANCHER — [PO]

1. **Le nom et le compte** [FIRM] (le doc est écrit avec un placeholder).
2. **Le fait produit** : règles exactes (drawdown trailing ou statique,
   heure de reset, règle de consistance, calendrier de payout, split,
   environnement simulé ou non). Rien ne se produit en authority avant.
3. **La palette et la grammaire visuelle** [FIRM] — parenté assumée avec
   LA LIGNE, ou rupture nette.
4. **La signature** de fin de caption (l'équivalent du "THE LINE — …").
5. **Grille en diagonale (3:1, recommandé) ou en colonne (2:1)** — §3.
6. **Les trois lead magnets** : lesquels existent déjà, lesquels sont à
   produire (RULES est le plus urgent — c'est le pilier éducation).

---

**Le plan concret des 12 premiers posts est dans `ROTATION_01.md`.**
