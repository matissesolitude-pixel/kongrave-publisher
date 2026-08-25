# BRIEF DE L'AUTEUR DES JSON — LA LIGNE

Ce fichier s'adresse à la session qui **écrit les épisodes** (`ligne/episodes/LN.json`),
pas à celle qui code les moteurs — celle-là lit `AGENT_MOTEURS.md`.
Il consigne ce qui a changé le **25 août 2026** et les corrections à ne plus refaire.
La loi éditoriale reste `SKILL_LIGNE_MOTEUR.md` ; ce document ne la remplace pas, il la complète
sur les points où la livraison précédente a fauté.

---

## 1. LA NUMÉROTATION — VÉRIFIER AVANT D'ÉCRIRE

La livraison du 25 août contenait un `L88.json` alors qu'un **L88 différent était déjà publié**
(« THE STOP THAT KEPT MOVING », sorti le 24 août). Déposé tel quel, il écrasait un épisode sorti
et créait un doublon de moteur.

Avant d'écrire le premier caractère, lister `ligne/episodes/` et `ligne/published/` sur `main`,
prendre le plus grand numéro existant, et commencer au suivant. Un identifiant déjà utilisé ne se
réemploie jamais, même si l'épisode qui le porte est mauvais.

## 2. LE DISPOSITIF — DEUX ÉPISODES CONSÉCUTIFS N'ONT JAMAIS LE MÊME

Les huit épisodes livrés le 25 août portaient tous `_dispositif: "MONTAGE PARALLÈLE"` et ouvraient
tous sur « Two traders… », alors que leur propre champ `_rules.dispositif` énonce la règle inverse.
Avec le L88 publié la veille, cela faisait neuf épisodes d'affilée sur la même ouverture.

Ils ont été envoyés quand même parce que la file était vide et que le compte ne publiait plus, mais
la règle reste : **on varie le dispositif d'un épisode à l'autre**. Ce qui est mesuré, et qu'il faut
garder, c'est l'ouverture — deux TRADERS, un geste concret et visible, une divergence annoncée dès
la première phrase. Le duel est une loi de la première seconde ; le montage parallèle n'est qu'une
manière de le mettre en images, et il en existe d'autres.

## 3. LA SIGNATURE DE FIN — « KONGRAVE », JAMAIS « @kongrave_ »

Le moteur de synthèse **vocalise l'arobase** : `@kongrave_` se prononce « at kongrave ». Le mot
parasite est audible, il a été repéré à l'oreille par le PO. Mesure : le jeton `@kongrave_` dure
0,74 s contre 0,51 s pour `KONGRAVE` seul.

Donc, dans `voice[4]`, écrire :

> Follow KONGRAVE — the mechanics nobody explains.

L'affichage à l'écran n'est pas concerné : le `@kongrave_` visible est codé en dur dans chaque
moteur, il ne vient pas du JSON. La règle vaut pour **tout texte destiné à être prononcé** : ni
arobase, ni tiret bas, ni symbole qui se lit à voix haute.

## 4. LA VOIX A CHANGÉ — LES ÉPISODES DOIVENT ÊTRE PLUS COURTS

Depuis le 25 août, la voix n'est plus George. C'est « LIGNE — Coach (A2) »
(`0jNVx6MiRPvEBiq9DBhH`), une voix construite par description, avec des réglages volontairement
agressifs décidés par le PO : `stability 0.25 · similarity 0.80 · style 0.50 · speed 1.12`.

Cette voix est **plus lente** : elle dit mille caractères en **65,7 secondes**, là où George tenait
le même texte en cinquante-cinq. Sur L91, l'épisode passe de 34,3 s à 40,2 s sans qu'un mot ait été
ajouté.

Or le format court est ce qui a fait monter la rétention de 19 % à 30 %. Le budget d'écriture change
donc, et c'est la contrainte la plus importante de ce document :

| Cible de durée | Budget total des 5 segments | Par segment |
|---|---|---|
| 30 s | **≈ 455 caractères** | ≈ 90 |
| 32 s | **≈ 485 caractères** | ≈ 97 |

Les épisodes L89 à L96 font 610 à 655 caractères : c'est vingt-cinq pour cent de trop pour cette
voix. Compter les caractères de `voice` avant de livrer, et couper dans le texte plutôt que
d'espérer que le rendu rattrape.

## 5. CE QUI NE CHANGE PAS

Le champ `total` du JSON ne fixe pas la durée : `build_ligne.py` mesure la voix segment par segment
et construit la timeline dessus, `total` ne sert qu'à rallonger la fin de moins de six secondes.
Écrire court est donc le seul moyen d'obtenir un épisode court.

Les phrases restent **entières** — proposition principale, virgule, subordonnée, point — jamais de
fragments télégraphiques. Le reel reste du TOFU sans mot-clé, son seul appel est l'abonnement,
prononcé en scène 5 et affiché au même moment. Il n'y a plus de narrateur : ne jamais écrire de
champ `_narrator` ni de `hook_gag`. Enfin, la loi de la première seconde et le seuil de skip à 52 %
restent le juge unique de la portée.
