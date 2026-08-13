# Références de style

Toute image déposée ici (`.png`, `.jpg`, `.jpeg`, `.webp`) est envoyée au modèle **en plus
du prompt**, comme référence de style. Le prompt décrit déjà le trait ; une référence
visuelle le verrouille beaucoup plus fermement — c'est le levier de qualité le plus fort
du générateur.

Le modèle reçoit la consigne explicite de **copier le rendu, pas le sujet ni la pose**.

## Ce qu'on y met

Des images qu'on **possède ou qu'on a licenciées** : rendus maison, planches déjà payées,
illustrations commandées. Le dossier est volontairement vide dans le dépôt : une image de
banque filigranée n'a rien à faire dans un repo, et la donner comme référence à imiter
n'est pas la même chose que s'en inspirer.

Deux à quatre images suffisent, toutes du même style. En mélanger plusieurs styles produit
une moyenne molle — l'inverse de l'effet recherché.

## Sans rien ici

Le générateur marche quand même : `STYLE_ENCRE` dans `illustrations.py` transcrit le style
trait par trait (trait fuselé, muscle creusé par paquets de traits courts, masses noires
traversées de réserves blanches, plis rayonnant des points de tension).
