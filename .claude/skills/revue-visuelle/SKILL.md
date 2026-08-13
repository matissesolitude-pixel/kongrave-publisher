---
name: revue-visuelle
description: Regarder ce qu'on a dessiné avant de le déclarer fini — rendu de frames et checklist de l'œil pour les moteurs LA LIGNE (ligne/engine/lNN.html), les props KONGRAVE et tout visuel HTML/SVG du repo. Charge cette skill dès qu'on écrit, corrige ou juge un moteur, une maquette, une frame DoD, une planche-contact, une illustration d'ouverture ; dès qu'on parle de "chevauchement", "étiquette coupée", "hors cadre", "frames", "maquette", "pré-vol", "ça rend quoi", "montre-moi"; et AVANT tout push d'un moteur. À utiliser même sans être nommée : dès qu'une conclusion visuelle est sur le point d'être tirée de la lecture du code au lieu d'une image rendue.
---

# REVUE VISUELLE — on ne juge jamais un dessin sur son code

La règle unique dont tout le reste découle, déjà gravée dans `ligne/AGENT_MOTEURS.md` :

> **Vérifie sur des frames RENDUES, jamais sur du raisonnement.**

Chaque défaut cité plus bas a été payé EN LIVE sur le feed (L23, L25, L27, L28) par
quelqu'un qui avait relu son code et l'avait trouvé correct. Le code se relit bien et
rend mal : `putCap` borne le texte mais rien ne borne un filet, une tige ou une flèche ;
une étiquette « posée dans une zone vide » l'est à l'écriture, plus à la frame 30 quand
l'objet animé est passé dessous. **L'œil est le seul contrôle qui attrape ça.**

## 1. RENDRE

```bash
python3 ligne/frames.py l70            # storyboard : ouverture/milieu/DoD × 5 scènes + PLANCHE.png
python3 ligne/frames.py l70 -s 4       # une scène suspecte
python3 ligne/frames.py l70 -s 4 -n 8  # 8 frames dedans, pour traquer un chevauchement mobile
python3 ligne/frames.py l70 -t 0 3.4   # des temps précis
```

Zéro dépendance, ~12 s pour un épisode entier. Sorties dans `/tmp/ligne_frames/<moteur>/`.
Puis **on ouvre les PNG avec l'outil Read** — surtout `PLANCHE.png`, qui met les 15 frames
côte à côte. Une erreur JS ne produit pas un PNG blanc : elle s'écrit EN TOUTES LETTRES
dans l'image.

Les durées de voix sont estimées (pas d'appel ElevenLabs) : ±10 %. Assez pour juger une
composition, pas une synchro à la frame.

## 2. LES DEUX CONTRÔLES SONT COMPLÉMENTAIRES

| | attrape | n'attrape pas |
|---|---|---|
| `frames.py` — **l'œil** | chevauchement, hors-cadre, composition, lisibilité | une scène figée |
| `preflight.sh` — **le scan** | écran quasi-vide, absence de progression (LOI 9) | tout ce qui est ci-dessus |

Les deux avant de pousser. Aucun ne remplace l'autre : le scan mesure des pixels, il
trouve « ça bouge » — pas « c'est lisible ».

## 3. LA CHECKLIST DE L'ŒIL

Dans l'ordre de fréquence observée sur ce repo. On la passe **frame par frame**, pas de mémoire.

1. **CHEVAUCHEMENT — LOI 10, le défaut n°1.** Rien ne se superpose : ni étiquette sur un
   dessin, ni étiquette sur étiquette. Pour chaque texte : *quel objet occupe ce (x, y)
   et sa bande verticale, à CE temps-là ?* Un objet qui se déplace passe sous une
   étiquette immobile → rendre 6-8 frames de la scène, pas une.
2. **HORS CADRE — et pas seulement le texte.** `putCap` mesure et borne les étiquettes ;
   **rien ne borne les traits**. Un filet de liaison, une tige, une flèche, une queue de
   courbe sortent du cadre sans que rien ne proteste. Zone sûre : **x ∈ [70, 1010]**,
   **y ∈ [560, 1450]** (l'UI Instagram mange le bas, le rail droit mange au-delà de x≈950).
   Suivre chaque trait jusqu'à son extrémité, sur la frame.
3. **LA MOITIÉ MORTE.** Sur la planche, une scène dont tout le contenu tient dans le tiers
   haut et laisse 900 px de papier vide en dessous est une scène ratée — même si le scan
   la valide. Le cadre est un portrait : il se compose sur toute sa hauteur utile.
4. **L'OUVERTURE QUASI VIDE — LOI 9 croisée LOI 1bis.** La colonne « ouverture » de la
   planche est la plus révélatrice de toutes : chaque scène doit ouvrir sur SES objets,
   **déjà pleins**, coupe franche. Une ouverture avec un seul objet perdu au milieu, c'est
   un draw-on progressif déguisé — et en S1, c'est l'émotion frame 0 manquée.
5. **LE TEST DES 0,2 SECONDE.** Regarder la frame comme on scrolle : la silhouette dit-elle
   quelque chose avant toute lecture ? Si comprendre exige de lire les étiquettes,
   la forme ne porte pas — c'est la LOI 1 (niveau 8 ans) qui casse, pas la typo.
6. **UN VERBE VISUEL DISTINCT PAR SCÈNE.** Les 5 colonnes DoD de la planche, côte à côte :
   si deux scènes montrent le même mouvement décliné, l'épisode est « radin ». C'est le
   seul contrôle qui se fait d'un coup d'œil — et seulement sur une planche.
7. **PALETTE.** Papier `#F2EFE7` · encre `#20242A` · toi/teal `#1E5F6E` · perte/gris
   `#474D50` · brun `#8A5323` **uniquement s'il existe un camp adverse**. Jamais de rouge.
   **Aucun chiffre à l'écran.**
8. **MARQUES ORPHELINES.** Petits traits flottants, restes d'une animation précédente,
   éléments à opacité résiduelle : ils ne coûtent rien au scan et salissent l'image.

## 4. QUAND UN DÉFAUT EST TROUVÉ

On corrige le moteur, **on re-rend, on re-regarde**. Une correction non revue n'est pas une
correction : L25 a été « corrigée » une fois sur le raisonnement, et a débordé à nouveau en
live. Le cycle se ferme sur une image, jamais sur une intention.

Pour une étiquette coupée, la réponse n'est jamais de raccourcir à l'estime : c'est
`putCap` copié **tel quel** depuis `l26.html` (il lit `getComputedTextLength`, letter-spacing
compris). Une estimation `longueur × facteur` est la cause de L23 puis L25 — on n'y revient pas.

## 5. AILLEURS QUE DANS LA LIGNE

`frames.py` est écrit pour les moteurs. Pour un `props/epNN.html`, un carrousel ou toute
page du repo, le même geste tient en une ligne — et la checklist ci-dessus s'applique
identiquement :

```bash
"$(python3 -c "import sys;sys.path.insert(0,'ligne');import frames;print(frames.find_chrome())")" \
  --headless=new --no-sandbox --disable-gpu --hide-scrollbars \
  --window-size=1080,1920 --virtual-time-budget=2500 \
  --screenshot=/tmp/vue.png "file://$PWD/props/ep24.html"
```

Puis Read sur `/tmp/vue.png`. `--no-sandbox` est obligatoire en conteneur (on y tourne en
root) ; sans lui Chromium refuse de démarrer et n'écrit aucun fichier.
