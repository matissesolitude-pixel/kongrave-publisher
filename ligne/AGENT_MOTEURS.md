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
4. **Étiquettes** — jamais par-dessus l'objet qu'elles nomment (à côté, au-dessus,
   en dessous, ou reliées par une accolade posée hors de l'objet). `putCap` réduit
   déjà la police pour que rien ne dépasse du cadre : le réutiliser tel quel.
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

## LE GESTE QUI COMPTE

Écrire `ligne/engine/lNN.html`, committer, **pousser sur `main`**. C'est le push qui
déclenche la fabrication (cron toutes les 2 h) puis la publication (cron toutes les 4 h,
cadence 6 h). Un moteur non poussé n'existe pas.

- Un moteur en cours ou écarté se renomme `lNN.html.wip` : la fabrication l'ignore proprement.
- **Ne jamais pousser pendant qu'un run `publish-ligne.yml` est en cours** : ce workflow
  fait un `git push` unique sans rebase, une collision lui fait perdre le journal après
  une publication réelle (risque de double post). Vérifier d'abord, et toujours pousser
  avec une boucle `git pull --rebase` + retry.
