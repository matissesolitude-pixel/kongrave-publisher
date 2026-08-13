---
name: dessin-personnage
description: Dessiner des personnages et des figures — corps, poses, anatomie, visages, séries d'illustrations cohérentes (exercices d'un programme sportif, mascotte, panneaux récurrents). Deux rigs vectoriels dans le repo (dessin/figure.py en manga/comics avec formes féminines, dessin/personnage.py en cartoon gros-nez) plus la route du modèle d'image. Charge cette skill dès qu'il s'agit de DESSINER au sens figuratif : "dessine un personnage", "illustre les exercices", style manga / comics / BD / Titeuf, un perso qui fait un squat, mascotte, character design, feuille de personnage, pose, silhouette, formes féminines, expression. NE PAS confondre avec les moteurs LA LIGNE (schémas animés) — ici on dessine un CORPS, pas un schéma.
---

# DESSIN DE PERSONNAGE

Une animation de LA LIGNE n'est pas un dessin : c'est un schéma qui bouge. Dessiner un
personnage, c'est un autre métier — un corps, un poids, une pose, une silhouette.

## CHOISIR L'OUTIL — et le dire avant de dessiner

| | `dessin/figure.py` | `dessin/personnage.py` | modèle d'image |
|---|---|---|---|
| Style | manga / comics | cartoon gros-nez | tout |
| Proportions | **7 têtes** | 3 têtes | libres |
| Formes du corps | **galbe, taille, hanches** | aucune (tubes) | oui |
| Cohérence sur 30 dessins | garantie | garantie | dérive |
| Contrôle de la pose | exact | exact | approximatif |
| Charme du trait à la main | non | non | **oui** |
| Dépendances | aucune | aucune | clé d'API |

**Par défaut, `figure.py`.** `personnage.py` ne sert que si un gag cartoon est
explicitement demandé — sa tête d'un tiers et ses membres d'épaisseur constante ne
peuvent montrer aucune anatomie.

**Une série d'illustrations d'exercices → un rig.** Trente poses du même personnage,
lisibles et cohérentes. **Une image unique qui doit avoir du charme → un modèle d'image.**
Ne jamais promettre un trait à la main et livrer du vectoriel.

## LE RIG FIGURE

```bash
python3 dessin/figure.py                  # planche des poses, ENCRÉE
python3 dessin/figure.py -p SQUAT
python3 dessin/figure.py --style comics   # trait plus épais, palette contrastée
python3 dessin/figure.py --hachures       # tramage dans les ombres
python3 dessin/figure.py --plat           # aplat vectoriel (à éviter : ce n'est pas de la BD)
python3 dessin/figure.py --svg SQUAT      # le SVG, pour retoucher ailleurs
```

Ajouter une pose = une entrée dans `POSES` : quinze articulations, un `vb` (cadrage), un
`headAng`. Le reste est déjà décidé.

**La boucle, dans cet ordre :**
1. Poser le squelette — on raisonne en articulations, jamais en courbes.
2. `check()` avant le rendu : il refuse les fautes structurelles (voir plus bas).
3. Rendre et **REGARDER** l'image (Read sur le PNG). Jamais conclure sur le code.
4. Corriger le **SQUELETTE**, pas le dessin. Rattraper une pose en déplaçant des courbes
   casse la cohérence de toute la série.
5. Re-rendre, re-regarder.

## LES QUATRE CHOSES QUI FONT UN CORPS

Chacune a été apprise en la ratant sur ce rig — ce sont les écarts entre un bonhomme et
une figure.

1. **7 TÊTES, PAS 3.** Le rapport tête/hauteur fait basculer à lui seul du cartoon vers le
   manga. Rien d'autre ne rattrape une tête trop grosse.
2. **MEMBRES FUSELÉS.** Chaque segment est une capsule à DEUX rayons — large à la cuisse,
   fin au genou ; large au mollet, fin à la cheville. Un tube d'épaisseur constante ne
   peut pas décrire une jambe, quelle que soit la pose.
3. **TORSE À PROFIL DISSYMÉTRIQUE.** De profil, les formes féminines ne sont pas *une*
   largeur : c'est un AVANT (poitrine, vers 0,30 de l'axe) et un ARRIÈRE (fessier, vers
   0,90) qui ne bombent pas au même endroit, séparés par une taille creusée vers 0,60.
   Deux profils de largeur indépendants — `FRONT` et `BACK`. Un torse symétrique est un tube.
4. **LA TENUE RÉVÈLE OU ANNULE.** Brassière + short, ventre nu : la taille se voit.
   Habiller le torse d'un seul aplat annule tout le point 3. Même logique sur la jambe :
   elle se dessine en CHAIR entière, le short ne couvre que le haut de cuisse — un aplat
   sombre du bassin à la cheville transforme la jambe en masse et efface le genou.

## L'ENCRAGE — ce qui sépare un aplat d'une planche de BD

Un aplat vectoriel, aussi juste soit-il d'anatomie, reste une découpe. Quatre gestes le
font basculer, dans cet ordre d'importance :

1. **L'OMBRE EN TACHE FRANCHE**, du côté opposé à la lumière. UNE source (haut-avant),
   jamais deux. **Le décalage de l'ombre est PROPORTIONNEL au rayon du volume** — un
   décalage constant met un bras fin entièrement dans l'ombre pendant qu'une cuisse reste
   à peine modelée. L'ombre est un croissant le long d'un bord, jamais une teinte globale.
2. **LE CONTOUR REPASSÉ CÔTÉ OMBRE.** L'encreur charge le trait là où la forme se détourne
   de la lumière ; un contour d'épaisseur constante est une signature d'ordinateur.
   **Se fait en repassant le contour RÉEL** (un `stroke` masqué) — surtout pas en
   grossissant la forme : les coutures entre capsules ressortent alors en pointes noires.
3. **L'OMBRE AU SOL.** Sans elle la figure flotte, quelle que soit la qualité du dessin.
4. **UN reflet dans les cheveux**, une seule bande. Deux reflets = deux sources = faux.

**Les hachures ne sont PAS l'encrage** (`--hachures`, désactivé par défaut). Un tramage à
45° appliqué uniformément lit comme du velours côtelé plaqué sur le corps, pas comme du
dessin. L'ombre de BD est une tache.

## LES FAUTES QUI TUENT UNE FIGURE

Les cinq premières sont refusées par `check()`.

1. **Os incohérents d'une pose à l'autre.** Fémur ~180 px, tibia ~175, bras ~128,
   avant-bras ~118. Un fémur qui change de longueur, et ce n'est plus le même personnage.
2. **Le crâne mange le cou** (sous ~62 px du cou au centre de tête). Le cou se dessine
   AVANT le torse : il sort des épaules, il ne se pose pas dessus.
3. **Articulation trop fermée** (sous ~58°) : les deux segments fusionnent en une masse.
4. **Pied sous le sol.** La semelle se pose SUR la ligne de sol.
5. **Articulation manquante** dans le squelette.
6. **Pas de main.** Sans mitaine, un bras finit en moignon arrondi. C'est le défaut qu'on
   ne voit pas en relisant le code et qui saute aux yeux sur l'image.
7. **Les deux bras superposés.** De profil, bras proche et bras lointain se confondent en
   planche. Les séparer FRANCHEMENT (coude plus bas, poignet en retrait de 50 px minimum)
   et assombrir le lointain.
8. **Ratio du viewBox ≠ ratio de la cellule** : le papier ne remplit plus le cadre, le
   personnage est rogné.

## LE STYLE

**Manga** — front bombé, **nez COURT** (s'il dépasse, ce n'est plus du manga), menton
pointu, gros œil en amande avec iris et point de lumière, sourcil séparé, bouche minuscule.
Contour fin (~9 px), aplats stricts, aucun dégradé. La profondeur vient d'une seule chose :
les membres lointains sont assombris.

**Comics** — même construction, contour épais (~13 px), palette plus contrastée et chaude.
`--style comics`.

**Gros-nez** (`personnage.py`) — l'inverse exact : tête énorme, nez qui DÉPASSE du crâne,
œil bien à l'intérieur, expression dans deux traits.

## CE QUE LES RIGS NE SAVENT PAS FAIRE

De l'aplat vectoriel propre et cohérent — **pas du dessin à la main**. Ni trait vivant, ni
déformation expressive, ni désordre organique. Le dire au lieu de le maquiller.

Pour s'en approcher : un modèle d'image, mais **avec une feuille de personnage** — la même
description exacte réutilisée à chaque appel (proportions, visage, palette, tenue, style de
trait) plus un rendu de référence joint. Sans feuille, la série dérive dès la troisième
image. Un rendu du rig fait une excellente référence de départ.
