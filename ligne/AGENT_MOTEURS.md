# AGENT MOTEURS — consigne de l'agent cloud (LA LIGNE)

Ce fichier est la consigne de travail de la routine cloud qui écrit les moteurs
d'animation de LA LIGNE **quand la machine de Matisse est éteinte**. Il est
autoportant : tout ce qu'il faut savoir est ici ou pointé depuis ici.

## LE PROBLÈME QU'ELLE RÉSOUT

`autoprod_ligne.py` ne fabrique QUE les épisodes dont le fichier moteur
`ligne/engine/lNN.html` existe **dans ce repo**. Les scénarios (`ligne/episodes/LNN.json`)
sont écrits jusqu'à L42, mais un JSON ne devient jamais une vidéo tout seul :
il faut un moteur. Sans moteur neuf, la file se vide et le compte cesse de publier.

## PRIORITÉ ABSOLUE : REPRODUIRE UN ÉPISODE REFUSÉ PAR META

Meta refuse parfois un épisode à la publication (`ProcessingFailedError`) **alors que le
fichier est prouvé valide** — même encodage, mêmes specs qu'un épisode accepté. C'est une
erreur **opaque et non déterministe** de Meta : on ne peut pas la corriger dans le fichier,
seulement **reproduire l'épisode de zéro** pour obtenir un nouveau master qui, lui, passera.

Quand le publisher a épuisé ses tentatives, il **retire le moteur** de l'épisode fautif :
`ligne/engine/lNN.html` est déplacé en `ligne/engine/lNN.html.refused_<date>` et l'épisode
est rangé dans `ligne/_hold/LNN_meta_<date>`. **Le moteur redevient donc « manquant ».**

**Ta règle :** si `episodes/LNN.json` existe, `engine/lNN.html` est **absent**, et qu'il
existe un `engine/lNN.html.refused_*` (ou un `_hold/LNN_meta_*`), ce N est une **REPRODUCTION**.
- Traite-le **en priorité** (c'est de toute façon le plus petit N manquant).
- **Le nouveau rendu DOIT DIFFÉRER MATÉRIELLEMENT du refusé.** Meta a rejeté ce flux d'octets
  précis ; un rendu quasi identique sera re-rejeté. Recode **réellement de zéro** (autres
  compositions / timings / choix d'objets, dans le même brief JSON) — ne recopie pas l'archive.
  Tu peux ouvrir le `.refused_*` uniquement pour voir ce qu'il ne faut **pas** refaire à l'identique.
- **Ne supprime jamais** les `.refused_*` : c'est l'historique des refus.
- La reproduction est **bornée automatiquement à 2 fois** : au-delà, le publisher abandonne et
  alerte pour intervention manuelle. Tu n'as rien à compter — code simplement le moteur manquant.



## ⛔ LOI : ZÉRO CHEVAUCHEMENT (la plus violée, la plus coûteuse)

**Rien ne se superpose à l'image.** Ni étiquette sur un dessin, ni étiquette sur une autre
étiquette, ni le narrateur sur un objet, un texte ou la boule teal.

**Pourquoi c'est une LOI et pas un goût :** un plan illisible fait décrocher. La lisibilité
fait le **watch time**, qui fait la **portée**. Un chevauchement ne coûte pas « un peu de
beauté » — il coûte des vues. C'est le défaut le plus répété de la série (L23/L25 étiquettes
coupées · L27/L28 étiquettes collées et texte sur dessin · L04/L24/L29 narrateur par-dessus le décor).

**Ce n'est plus une affaire de vigilance, c'est une porte :**
- `putCap` **mesure** la largeur réelle et borne le centre → un texte ne peut plus être coupé.
- Le narrateur **cherche une zone libre avant de se dessiner** (`placeClear` : il mesure les
  bounding boxes de ce qui est déjà à l'écran, se décale, rétrécit, et **DISPARAÎT** si rien
  n'est libre). Il reste aussi **entier dans le cadre** : s'écarter hors champ n'est pas une solution.
- Toi, tu restes responsable du **placement des étiquettes** : avant d'en poser une, demande-toi
  quel objet occupe ce (x, y) et sa bande verticale.

**Vérifie sur des frames RENDUES, jamais sur du raisonnement.**


## LE NARRATEUR MR DOLLAR

> ### ⛔⛔ EN PAUSE — décision du 26/07/2026 — NE PAS AJOUTER LE NARRATEUR
> Matisse a mis Mr Dollar en pause : « on arrête Mr Dollar pour le moment parce qu'on n'arrive
> pas à bien l'animer ». **N'ajoute AUCUN narrateur dans les nouveaux moteurs** : pas de
> `/*INCLUDE:narrator*/`, pas de `MrD.enter`, rien. L'épisode repose sur la mécanique
> « émotion par objets » SEULE. Le reste de cette section ne s'applique QUE si la pause est levée.

Mr Dollar est **la voix** du Reel. Il **apparaît pour parler**, puis il s'efface. C'est tout.

> ### ⛔ PLUS DE GAGS — décision du 24/07/2026
> Les primitives de gag (`bumpInto`, `fall`, `crushedBy`, `zoom`…), l'agent, la réaction et
> le raccord sont **supprimés**. Le champ `hook_gag` des JSON n'est plus lu. Trop de choix
> produisait des plans illisibles : on garde ce qui marche — il arrive, il parle, il désigne,
> il s'en va. `MrD.gag()` existe encore par compatibilité mais **ignore** ses arguments de gag.

**UNE SEULE LIGNE à écrire**, après la création de `SVG` :

```
    /*INCLUDE:narrator*/
```

`build_ligne` y injecte la bibliothèque narrateur, les poses vectorisées, la carte des yeux
(clignement) et l'objet `MrD`, déjà branché sur l'amplitude de la voix. **N'inline JAMAIS
les SVG des poses à la main** : c'est 300 Ko et une source d'erreurs.

**Le faire entrer — la seule API :**
```js
// u = temps local de l'apparition (0 = il arrive)
MrD.enter(u, {t:t, routine:'designe', lookAt:CX, rest:{x:180,y:1430,h:220}, op:gf});
```
- `routine` : `designe` (il montre puis laisse regarder) · `explique` · `attend` · `reagit`
  · `doute` · `constate`. Chaque pose est une **intention**, jamais une variation décorative.
- `lookAt` : abscisse de ce qu'il désigne — il **se tourne et pointe du bon côté**. Omets-le
  s'il ne désigne rien.
- `rest` : où il aimerait se tenir. La bibliothèque **corrige** cette position si la zone est
  occupée (loi zéro chevauchement) : il se décale, rétrécit, ou disparaît.

**Ailleurs dans l'épisode :**
- `MrD.pointAt('point', t, x, y, h, op, cibleX)` — désignation ponctuelle hors `enter`. Le sens
  est calculé. **N'utilise JAMAIS `say('point')` pour désigner** : les poses visent à droite
  par défaut, le sens serait faux une fois sur deux.
- `MrD.say('idle'|'walk'|'wave_hip', t, x, y, h, op, flip)` — présence sans désignation.
- `MrD.hide()` — dès que la démonstration a besoin de la place.

**Règles :** toujours en **ENCRE**, jamais en teal (le teal est réservé au spectateur). Il est
**PETIT** et s'écarte ; le schéma prime toujours. **AUCUN gabarit de placement** — ses
apparitions sont des ÉVÉNEMENTS décidés épisode par épisode, jamais un rythme prévisible.
Il ne porte jamais le fusil de Tchekhov. Il n'apparaît pas en S4.

**Vie continue :** il ne dispense de rien. Une scène où il sort doit rester vivante SANS lui —
c'est le défaut le plus fréquent (scène figée dès son départ, attrapée par le scan fail-loud).

## LA LOI

**`ligne/SKILL_LIGNE_MOTEUR.md` est la loi.** Elle se lit EN ENTIER avant d'écrire
une seule ligne. Les points qui font échouer un moteur, dans l'ordre de fréquence :

1. **Émotion dès la frame 0** — la scène 1 s'ouvre à son point de tension maximal.
   Aucun draw-on progressif : l'image 1 EST quelque chose, elle ne se remplit pas
   pour le devenir. La 1re ligne de la question est écrite dès t=0.
2. **Un verbe visuel DISTINCT par scène** — jamais le même mouvement décliné 5 fois.
3. **Vie continue** — aucune tenue figée hors image finale. Attention :
   - une variation d'**opacité n'est pas un mouvement** (le scan compare des pixels,
     il faut du déplacement de POSITION) ;
   - une **sinusoïde unique a une vitesse nulle à ses extrêmes** : toute vie continue
     s'écrit à DEUX harmoniques, `a*sin(w1*u) + b*sin(w2*u)` ;
   - une scène qui **ouvre sur peu d'objets** = écran quasi vide. Coupe franche :
     la scène ouvre sur SES objets, déjà pleins, dès sa première frame.
4. **Étiquettes — LE POINT LE PLUS FRAGILE (coupé / chevauché en LIVE sur L23, L25, L27, L28).**
   - `putCap` **MESURE** désormais la largeur réelle (`getComputedTextLength`, qui compte le
     letter-spacing) et borne le centre par cette demi-largeur : un texte ne peut plus être coupé
     au bord. **Copie-le TEL QUEL depuis `l26.html`.** Ne reviens JAMAIS à une estimation
     `longueur × facteur` : elle ignore le letter-spacing et fait déborder (cause du bug L23/L25).
   - **Jamais par-dessus un dessin.** Une étiquette se pose dans une **zone VIDE** (gouttière,
     au-dessus, en dessous), **jamais dans la colonne d'un objet animé** (barre, ticks, flèche,
     pastille, ligne). Avant de la placer, demande-toi : *quel objet occupe ce (x, y) et sa bande
     verticale ?* Si un objet y passe, déplace l'étiquette. (Bug L28 : ticks à travers le texte.)
   - **Deux étiquettes gauche/droite** : chacune reste dans SA moitié — gauche `cx ≤ 380`,
     droite `cx ≥ 700` — elles ne se rejoignent jamais au centre.
   - **Deux étiquettes voisines** (ex. « GOOD DECISION » / « BAD DECISION ») : un vrai espace entre
     elles (mesure + écart, ou empile-les). Jamais collées « GOOD DECISIONBAD DECISION » (bug L27).
   - **Texte DANS une forme** (pastille, badge) : il doit tenir dans la forme — élargis la forme à
     la largeur mesurée, ou raccourcis le texte. Sinon la forme le coupe (« FROM A BAD DAY » →
     « ROM A BAD D » sur L27).
5. **Cadrage** — tout ce qui compte reste entre y≈560 et y≈1450 (l'UI d'Instagram
   mange le bas, et le rail droit au-delà de x≈950).
6. **Palette** — papier `#F2EFE7`, encre `#20242A`, toi/teal `#1E5F6E`,
   perte/gris `#474D50`. **Jamais de brun, jamais de rouge, aucun chiffre à l'écran.**

## LE CONTRAT TECHNIQUE DU MOTEUR

Un moteur est un fichier HTML autoportant. Le plus simple et le plus sûr :
**copier la structure d'un moteur récent validé** (`ligne/engine/l25.html` ou
`l26.html`) et ne changer que le contenu des cinq scènes.

Invariants à ne pas toucher :
- `<html data-resolution="portrait" data-fps="30">`, SVG `viewBox="0 0 1080 1920"` ;
- les marqueurs `__TOTAL__`, `__SCENES__`, `__SPEC__` (substitués à la fabrication) ;
- `window.__timelines['main']` alimenté par une timeline GSAP pilotant `clock.t` ;
- les fonctions `s1..s5` exportées via `const RENDER={s1,s2,s3,s4,s5}`.

Le JSON de l'épisode donne, scène par scène : `clarity` (l'histoire en une phrase),
`beats` (le déroulé), `dod` (ce que l'image doit dire sans le son), `cast`, et les
`_rules` (doctrine, interdits, palette). **Le champ `caption` du JSON ne se touche
jamais** — il part tel quel sur Instagram.

## LE CONTRÔLE AVANT DE POUSSER

`build_ligne.py` fait ÉCHOUER la fabrication si, pendant une voix, l'image reste
plus de 1,5 s sans progression, ou plus de 0,4 s quasi vide (<0,4 % d'encre).
Un échec = ~10 min de runner perdues et aucun épisode en file.

Si Chromium est disponible dans l'environnement, passer `ligne/preflight.sh lNN LNN.json`
(il rend des paires de frames à 1/15 s et applique les mêmes seuils). Un point isolé
sous le seuil est tolérable ; **trois sondes consécutives en défaut ne le sont pas**.

Si Chromium n'est pas disponible : relire le moteur scène par scène en se demandant,
pour chaque tenue longue, *quel objet se déplace réellement à chaque frame*. S'il n'y
en a aucun, la scène est morte — ajouter un mouvement de position à deux harmoniques.

## LES SFX « PAR TOUCHE » (à ajouter dans le JSON de chaque nouvel épisode)

Les Reels portent des **effets sonores minimaux** : des ACCENTS sur les temps-clés,
mixés SOUS la voix. **Jamais un tapis sonore.** Retenue absolue : une poignée de touches
par épisode, sur les vrais beats. La voix reste toujours maître.

**Comment les poser :** un tableau `sfx` dans le JSON de l'épisode :
```json
"sfx": [ {"sc": 4, "t": 1.0, "s": "tick"}, {"sc": 5, "t": 4.0, "s": "resolve"} ]
```
- `sc` = numéro de scène (1-based) · `t` = décalage EN SECONDES depuis le début de la scène
  (relatif = robuste aux variations de durée de la voix) · `s` = nom du son.
- `build_ligne` synthétise chaque son (aucune banque externe) et le mixe sous la voix.

**Palette et quand l'utiliser :**
- `pop` → un élément se dessine / apparaît.
- `whoosh` → une révélation, un balayage, un rideau, un pivot.
- `thunk` → un impact bas : quelque chose se pose, s'effondre, pèse, plonge.
- `tick` / `tickhi` → un beat, un pas, un compteur qui monte (`tickhi` pour le climax aigu).
- `riser` → une courte montée de tension avant un payoff.
- `resolve` → note calme UNIQUE sur l'image finale tenue.

**Règle :** chaque touche doit correspondre à un ÉVÉNEMENT visible à l'écran (même logique
que le narrateur : le son souligne une cause visible, il n'invente rien). ~6 à 12 touches max.

## LE GESTE QUI COMPTE

Écrire `ligne/engine/lNN.html`, committer, **pousser sur `main`**. C'est le push qui
déclenche la fabrication (cron toutes les 2 h) puis la publication (cron toutes les 4 h,
cadence 6 h). Un moteur non poussé n'existe pas.

- Un moteur en cours ou écarté se renomme `lNN.html.wip` : la fabrication l'ignore proprement.
- **Ne jamais pousser pendant qu'un run `publish-ligne.yml` est en cours** : ce workflow
  fait un `git push` unique sans rebase, une collision lui fait perdre le journal après
  une publication réelle (risque de double post). Vérifier d'abord, et toujours pousser
  avec une boucle `git pull --rebase` + retry.
