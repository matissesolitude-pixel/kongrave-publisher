# NARRATEUR — "MR DOLLAR"

Le narrateur de THE LINE. **Son corps EST le signe `$`** (logique Mr DNA : le personnage
*est* son sujet). Les yeux sont posés dans la boucle haute du `$`, les bras tuyau et les
jambes sortent du `$`. Il n'y a **pas** de tête séparée, et le `$` n'est **pas** un motif
posé sur un ventre.

## Origine

Poses dessinées par Gemini (model sheets validées par le PO), **vectorisées** (vtracer,
seuil N&B puis trace binaire) et recolorées en encre `#20242A`. On ne redessine JAMAIS le
personnage à la main : on part toujours de l'art validé.

## La bibliothèque (18 poses = 9 × 2 jeux)

Deux jeux d'expression, interchangeables :
- **`_wide`** — sourire large → **accueil, présentation, hook**
- **`_soft`** — sourire discret → **explication, sérieux, démonstration**

| Fichier | Pose | Usage |
|---|---|---|
| `idle_*` | debout, bras le long du corps | présence neutre, il écoute |
| `idle_arms_down_*` | debout, variante | alternance, évite la boucle figée |
| `point_*` | **bras tendu, index pointé (vers la droite)** | **désigner le schéma** (miroir horizontal pour pointer à gauche) |
| `present_*` | deux bras ouverts | présenter, « voilà », ouvrir une scène |
| `wave_*` | une main levée | entrée / sortie, salut |
| `wave_hip_*` | main levée + main sur la hanche | assurance, aparté |
| `front_*`, `front_b_*` | `$` de face, plein pied | posture statique, gros plan |
| `walk_*` | en marche | déplacement d'un point à un autre |

## Règles d'usage (LOI)

- **TOUJOURS en encre `#20242A`. JAMAIS en teal** — le teal est réservé à TOI (le spectateur).
  Le narrateur est extérieur : il montre, il ne subit rien.
- **Petit à l'écran** : il ne domine jamais le schéma. Placé sur un côté, il **s'écarte**
  quand la démonstration a besoin de place.
- **Son regard suit ce qu'il désigne** — c'est ce qui donne l'intention. Pointer sans
  regarder ne marche pas.
- **Il ne remplace jamais un élément du fusil de Tchekhov.** Il accompagne, il ne porte
  pas la démonstration.
- **Absent en S4** (tension maximale) si sa présence dilue le choc. À arbitrer épisode par épisode.
- **Jamais la même boucle d'un épisode à l'autre** : on varie les poses et les entrées.
- **LA TAILLE EST UN OUTIL DE MISE EN SCÈNE.** Elle n'est pas fixe :
  · s'il **gêne** un texte ou un objet de la démonstration → on le **rapetisse** (ou on le déplace) ;
  · si le **hook** y gagne en impact → on l'**agrandit** franchement à l'ouverture, puis il
    reprend une taille discrète dès qu'il passe la main.
  Le schéma prime toujours : la taille du narrateur s'ajuste à lui, jamais l'inverse.

## Intégration technique

Chaque pose est un SVG autonome (chemins pleins en encre, fond transparent). Dans un moteur :
on injecte la pose voulue dans un `<g>` positionné/mis à l'échelle, et on **change de pose**
au beat (swap), avec translations/échelle pour les entrées, sorties et gros plans.
Le gros plan du hook = la même pose, simplement agrandie et recadrée.
