# Coefficient

Petite app mobile de calcul calories / protéines, avec compteur de la journée
et suivi du poids.

**En ligne :** https://claude.ai/code/artifact/ae30f89f-c8d2-4b82-a2b6-8784aed76710

## La méthode

- **Calories** — poids en livres × un coefficient de 7 à 21. La base par défaut
  est le **poids objectif** (on mange comme la personne qu'on veut devenir) ;
  un bouton bascule sur le poids actuel.
- **Paliers** — 7–9 déficit agressif · 10–12 perte de poids · 13–15 maintien ·
  16–18 léger surplus · 19–21 surplus franc.
- **Protéines** — poids actuel en kilos × 2. Version métrique du « 1 g par livre »,
  qui donne environ 10 % de plus.
- **Viande** — une livre (454 g) de bœuf, poulet, canard ou crevette ≈ 100 g de
  protéines. Approximation : compter 90 à 110 g selon la pièce et la cuisson.
- **Conversion** — kg × 2,20462 = lb.

Une fois les protéines atteintes, les calories restantes se dépensent librement.

## Les trois écrans

| Écran | Ce qu'il fait |
|---|---|
| Calcul | Poids actuel, poids objectif, taille. Curseur de coefficient sur un fléau gradué 7 → 21. Sortie : kcal/jour, g de protéines, grammes de viande équivalents, calories libres, IMC actuel → IMC à l'objectif |
| Journée | Calories restantes avant le plafond, jauge de protéines, 24 aliments à ajouter d'un tap (protéines / féculents / plaisirs), saisie libre, liste du jour. Remise à zéro automatique au changement de date |
| Suivi | Journal de pesées, courbe de poids avec la ligne d'objectif, tendance 7 jours et depuis le début, jauge départ → cible |

## Le fichier

`app.html` est le corps de l'artifact : l'enveloppe `<!doctype html>` / `<head>` /
`<body>` est ajoutée à la publication, le fichier n'en contient donc pas. Pour le
republier après modification, passer l'URL ci-dessus afin de garder le même lien.

Les données vivent dans le `localStorage` du navigateur qui consulte la page
(clé `coefficient.v2`). Rien n'est envoyé au serveur, et deux personnes ouvrant le
même lien ont chacune leurs propres chiffres.

Règle empirique de terrain, pas un avis médical.
