# Coefficient

Petite app mobile qui applique la méthode Hormozi : calories et protéines
calculées sur le **poids cible**, calories libres une fois la viande payée,
compteur de la journée et suivi du poids.

**En ligne :** https://claude.ai/code/artifact/ae30f89f-c8d2-4b82-a2b6-8784aed76710

## La méthode

Reprise de la transcription de la vidéo, avec ses propres chiffres en test
de référence (200 lb, coefficient 10, dinde hachée → 2 000 kcal, 200 g de
protéines, 2 lb de viande à 1 120 kcal, **880 kcal libres**).

1. **Calories** — poids en livres × un coefficient de 7 à 21.
   Ici la base est le **poids cible**, pas le poids du jour : le budget ne
   bouge plus tant que la cible ne bouge pas. Le poids actuel ne sert qu'au suivi.
2. **Paliers, de trois en trois** — 7–9 perte extrême · 10–12 perte modérée ·
   13–15 maintien · 16–18 prise modérée · 19–21 prise extrême.
3. **Protéines** — 1 gramme par livre.
4. **Viande** — une livre de dinde, poulet, bœuf maigre, crevette ou poisson
   blanc ≈ 100 g de protéines. Il en faut donc autant de livres que de
   centaines de grammes de protéines visées.
5. **Calories libres** — on retire du budget ce que la viande coûte
   *réellement* (gras compris), pas 4 kcal par gramme de protéine. Le reste se
   dépense librement.

## Les trois écrans

| Écran | Ce qu'il fait |
|---|---|
| Calcul | Poids cible et taille. Curseur de coefficient sur un fléau gradué 7 → 21. Choix de la source de protéines (kcal par livre). Sortie : kcal/jour, g de protéines, livres et grammes de viande, coût de cette viande, et le grand chiffre des calories libres |
| Journée | Calories restantes avant le plafond, jauge de protéines, 26 aliments à ajouter d'un tap (protéines / féculents / plaisirs), saisie libre. Remise à zéro automatique au changement de date |
| Suivi | Journal de pesées, courbe avec la ligne d'objectif (épinglée au bord du cadre si la cible sort de l'échelle), tendance 7 jours et depuis le début, jauge départ → cible, poids du jour et IMC |

## Le fichier

`app.html` est le corps de l'artifact : l'enveloppe `<!doctype html>` / `<head>` /
`<body>` est ajoutée à la publication, le fichier n'en contient donc pas. Pour le
republier après modification, passer l'URL ci-dessus afin de garder le même lien.

Les données vivent dans le `localStorage` du navigateur qui consulte la page
(clé `coefficient.v2`). Rien n'est envoyé au serveur, et deux personnes ouvrant le
même lien ont chacune leurs propres chiffres.

Méthode empirique, pas un avis médical.
