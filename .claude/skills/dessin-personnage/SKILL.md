---
name: dessin-personnage
description: Dessiner des personnages et des figures — corps, poses, visages, séries d'illustrations cohérentes (exercices d'un programme sportif, mascotte, panneaux récurrents). Deux routes assumées : le rig vectoriel du repo (dessin/personnage.py) et le modèle d'image piloté par feuille de personnage. Charge cette skill dès qu'il s'agit de DESSINER au sens figuratif : "dessine un personnage", "illustre les exercices", "style Titeuf / gros nez / BD", "un perso qui fait un squat", mascotte, character design, feuille de personnage, pose, anatomie, expression. NE PAS confondre avec les moteurs LA LIGNE (schémas animés) — ici on dessine un CORPS, pas un schéma.
---

# DESSIN DE PERSONNAGE

Une animation de LA LIGNE n'est pas un dessin : c'est un schéma qui bouge. Dessiner un
personnage, c'est un autre métier — un corps, un poids, une pose, une expression.
Cette skill couvre ce métier-là.

## LES DEUX ROUTES — choisir en connaissance de cause

| | **Rig vectoriel** (`dessin/personnage.py`) | **Modèle d'image** |
|---|---|---|
| Cohérence sur 30 dessins | garantie — même rig, mêmes proportions | dérive à chaque image |
| Contrôle de la pose | exact (on pose les articulations) | approximatif, par le prompt |
| Correction ciblée | oui, on change une coordonnée | non, on relance et on espère |
| Modifiable après coup | oui (SVG, recolorable, rescalable) | non |
| Charme du trait à la main | **non** — aplat vectoriel propre | oui |
| Dépendances | aucune | clé d'API |

**Une série d'illustrations d'exercices → le rig.** C'est exactement son cas d'usage :
trente poses du même personnage, lisibles, cohérentes, corrigeables une par une.

**Une illustration unique qui doit avoir du charme → le modèle d'image.** Le repo a déjà
`google-genai` en dépendance (scènes narratives KONGRAVE, `gen_seg4_narratif.py`) ; le
connecteur Adobe/Firefly est l'autre voie (skill `connecteurs-creatifs`).

**Dire lequel on prend, et pourquoi, avant de dessiner.** Promettre du Zep et livrer du
vectoriel plat est la façon la plus sûre de décevoir.

## LE RIG — comment on s'en sert

```bash
python3 dessin/personnage.py              # planche de toutes les poses
python3 dessin/personnage.py -p SQUAT     # une pose
python3 dessin/personnage.py --svg SQUAT  # le SVG, pour retoucher ailleurs
```

Ajouter une pose = ajouter une entrée dans `POSES` : quinze articulations et un `vb`
(cadrage). Le corps, le contour, la palette et le style de tête sont déjà décidés.

**La boucle, dans cet ordre — elle n'est pas négociable :**

1. **Poser le squelette.** On raisonne en articulations, jamais en courbes.
2. **`check()` avant de rendre.** Le script refuse en silence trois fautes structurelles
   qu'aucun coup de crayon ne rattrape (voir plus bas).
3. **Rendre et REGARDER l'image** (Read sur le PNG). Jamais conclure sur le code.
4. **Corriger le SQUELETTE, pas le dessin.** Une jambe qui se lit mal est une jambe mal
   articulée — la rattraper en déplaçant des courbes casse la cohérence de la série.
5. Re-rendre, re-regarder. Une correction non revue n'est pas une correction.

## LES FAUTES QUI TUENT UNE FIGURE

Les trois premières sont vérifiées par `check()` — elles ont toutes été payées en essais
successifs sur ce rig, pas inventées.

1. **Le crâne mange le cou.** Une grosse tête posée à moins de ~106 px du cou l'avale
   entièrement : le personnage devient une tête sur un tronc. Le cou se dessine AVANT le
   tronc (il sort de la masse des épaules, il ne se pose pas dessus).
2. **L'articulation trop fermée.** Sous ~62° au genou ou au coude, les deux segments —
   épais de 62 px contour compris — fusionnent en une seule masse illisible. Un squat
   profond se dessine cuisse quasi horizontale, tibia incliné, genou au-dessus du pied.
3. **Le pied qui flotte ou s'enfonce.** La semelle se pose SUR la ligne de sol, à ±8 px.
4. **Le ratio du viewBox ≠ celui de la cellule.** Le papier ne remplit plus le cadre et le
   personnage se retrouve décadré ou rogné. Un cadrage se vérifie à l'image, toujours.
5. **Les deux mains au même endroit.** En vue de profil, bras proche et bras lointain
   finissent en pâté. Décaler franchement le bras lointain (coude plus bas, poignet en
   retrait) — et l'assombrir.
6. **Pas de masse d'épaule / de bassin.** Sans les disques d'attache, les membres sortent
   du tronc comme des bâtons plantés.
7. **Les cheveux sur l'œil.** La calotte s'arrête au-dessus du sourcil, sinon le visage
   perd toute expression.

## LE STYLE « GROS NEZ » (famille Titeuf, école franco-belge)

Ce que le rig applique, et ce qu'il faut respecter en ajoutant des poses :

- **Tête énorme** — ~1/3 de la hauteur visible. C'est elle qui porte l'émotion.
- **Le nez DÉPASSE du crâne**, en disque, contour compris. C'est la signature de l'école.
- **Œil bien à l'intérieur du crâne**, jamais collé au nez. Un seul œil de profil.
- **Contour noir uniforme et épais** (13-14 px sur un corps de ~530 px), bouts ronds.
- **Aplats stricts** : aucun dégradé, aucune hachure, aucune ombre portée. La profondeur
  vient d'une seule chose : les membres lointains sont assombris.
- **L'expression tient dans deux traits** — le sourcil et la bouche. Rien d'autre.
- **Membres = traits épais à bouts ronds.** On ne décrit jamais le contour d'un bras.

## CE QUE LE RIG NE SAIT PAS FAIRE

Il produit du vectoriel propre et cohérent, **pas du dessin à la main**. Il n'a ni le trait
vivant, ni la déformation expressive, ni le désordre organique d'un vrai illustrateur. Le
dire franchement au lieu de le maquiller.

Pour s'en rapprocher : passer par un modèle d'image, mais **avec une feuille de personnage**
(la même description exacte réutilisée à chaque appel : proportions, visage, palette,
vêtement, style de trait) et un rendu de référence joint. Sans feuille, la série dérive dès
la troisième image et le personnage n'est plus le même — c'est précisément le problème que
le rig résout.
