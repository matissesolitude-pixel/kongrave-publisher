# Fader

Petite app mobile qui applique la méthode Hormozi : un fader vertical règle le
coefficient, l'app en tire tes calories et tes protéines, et le reste se dépense
comme tu veux.

**En ligne :** https://claude.ai/code/artifact/ae30f89f-c8d2-4b82-a2b6-8784aed76710

## La méthode

Reprise de la transcription de la vidéo, avec ses chiffres en test de référence
(200 lb, coefficient 10, dinde hachée → 2 000 kcal, 200 g de protéines,
2 lb de viande, ~880 kcal libres).

1. **Calories** — poids visé en livres × un coefficient de 7 à 21. La base est le
   poids cible, pas celui du jour : le budget ne bouge plus tant que la cible ne
   bouge pas.
2. **Paliers, de trois en trois** — 7–9 perte extrême · 10–12 perte modérée ·
   13–15 maintien · 16–18 prise modérée · 19–21 prise extrême.
3. **Protéines** — un gramme par livre.
4. **Viande** — une livre de dinde, poulet, bœuf maigre, crevette ou poisson blanc
   ≈ 100 g de protéines. Le raccourci ne vaut que pour la viande maigre : chaque
   source porte sa densité réelle et affiche ce que lui coûtent 100 g de protéines.
5. **Mélange** — on combine autant de sources qu'on veut ; ajouter une source
   comble le manque ou rééquilibre l'ensemble.
6. **Calories libres** — on retire du budget ce que la source coûte *réellement*,
   gras compris, pas 4 kcal par gramme de protéine.

## Direction artistique

Une console de réglage, pas un tableau de bord.

- **Le fader** est vertical, pleine hauteur, avec une **rampe divergente** :
  froid en bas (déficit), neutre au milieu (maintien), chaud en haut (surplus).
  L'accent de toute l'app suit la position du curseur — l'app refroidit quand tu
  descends, chauffe quand tu montes.
- **Palette validée** avec `dataviz/scripts/validate_palette.js` : contrastes ≥ 4,3
  sur les deux fonds, séparation minimale 10,8. Un arc-en-ciel à cinq paliers ne
  passe pas les tests de séparation, d'où la forme divergente.
- **Type** — Big Shoulders Display pour les chiffres, Karla pour le texte,
  Chivo Mono en pincée.
- **Deux jauges, deux sens** : bleu pour un plafond de calories qui se remplit,
  vert pour une cible de protéines à atteindre.

## Les trois écrans

| Écran | Ce qu'il fait |
|---|---|
| Réglage | Le fader, le poids visé, la taille, le composeur de sources de protéines, et le grand chiffre des calories libres |
| Journée | Calories restantes, jauges segmentées, cartes d'aliments à taper avec compteur, saisie libre. Remise à zéro au changement de date |
| Courbe | Pesées, courbe avec la ligne de cible, tendances, route vers la cible, IMC, journal |

## Le fichier

`app.html` est le corps de l'artifact : l'enveloppe `<!doctype html>` / `<head>` /
`<body>` est ajoutée à la publication. Pour le republier après modification,
passer l'URL ci-dessus afin de garder le même lien.

Les données vivent dans le `localStorage` du navigateur qui consulte la page
(clé `coefficient.v2`). Rien n'est envoyé au serveur.

Méthode empirique, pas un avis médical.
