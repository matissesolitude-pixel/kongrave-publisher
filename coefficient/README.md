# Coefficient

Petite app mobile de calcul calories / protéines, avec objectif et suivi du poids.

**En ligne :** https://claude.ai/code/artifact/ae30f89f-c8d2-4b82-a2b6-8784aed76710

## La règle

- **Protéines** — poids en livres × 1 = grammes de protéines par jour.
- **Calories** — poids en livres × un coefficient entre 7 et 21.
  Bas pour sécher, autour de 14 pour tenir, haut pour prendre.
- **Conversion** — kg × 2,20462 = lb.

## Les trois écrans

| Écran | Ce qu'il fait |
|---|---|
| Calcul | Poids en kg, curseur de coefficient sur un fléau gradué 7 → 21, lecture kcal + g de protéines |
| Objectif | Direction (sécher / maintenir / prendre), poids de départ et cible, jauge d'avancement |
| Suivi | Journal de pesées, courbe de poids avec ligne de cible, tendance 7 jours et depuis le début |

## Le fichier

`app.html` est le corps de l'artifact : l'enveloppe `<!doctype html>` / `<head>` / `<body>`
est ajoutée à la publication, le fichier n'en contient donc pas. Pour le republier
après modification, il faut passer l'URL ci-dessus afin de garder le même lien.

Les données sont stockées dans le `localStorage` du navigateur qui consulte la page.
Rien n'est envoyé au serveur, et deux personnes ouvrant le même lien ont chacune
leurs propres chiffres.

Règle empirique de terrain, pas un avis médical.
