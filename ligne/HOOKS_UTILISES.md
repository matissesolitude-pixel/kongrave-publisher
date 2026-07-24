# HOOKS UTILISÉS — registre d'unicité de Mr Dollar

## ⛔ LA LOI D'UNICITÉ (absolue)

**Le personnage ne fait JAMAIS deux fois la même chose. Aucun hook ne se répète, sur aucun
épisode, jamais.**

**Primitive ≠ hook.** Une primitive est un verbe technique (`fall`, `bumpInto`, `contrast`…).
Le HOOK est la **combinaison complète** :

> `primitive × agent × réaction × temps × raccord`

L'agent étant l'objet **propre** de l'épisode, deux hooks partageant une primitive n'ont
visuellement rien en commun. Exemple : `fall` dans un gouffre, `fall` sous une pile qui
s'effondre, `fall` de marche en marche — trois ouvertures sans aucun rapport.

**Avant d'écrire un nouveau hook, on le compare à ce registre.** Sont INTERDITS :
1. une combinaison complète déjà enregistrée ;
2. la même **primitive avec le même agent** ;
3. la même paire **réaction + raccord** sur deux épisodes consécutifs.

*La non-répétition n'est pas une intention, c'est une porte* — `validate.py --json LXX`
doit refuser un épisode dont le `hook_gag` viole une de ces trois règles.

## Le bloc dans le JSON (scène S1)

```json
"hook_gag": {
  "primitive": "bumpInto",
  "agent": "le rideau qui masque la droite",
  "reaction": "sonné",
  "temps": "en plein geste",
  "raccord": "il se relève et pointe le ?"
}
```

`primitive` est lue par `ligne/assets/narrator-gags.js`. `agent` **nomme** l'objet (c'est lui
qui porte l'unicité) ; ses coordonnées réelles sont fournies par le moteur, puisque l'objet y
est déjà codé. `temps` documente l'état à la frame 0 (déjà arrivé / imminent / en plein geste).

## Registre

| Épisode | Primitive | Agent | Réaction | Temps | Raccord |
|---|---|---|---|---|---|
| **L44** — WHERE THE CHART ENDS | `bumpInto` | le rideau qui masque la droite | sonné | en plein geste | il se relève et pointe le ? |

<!-- Une ligne par épisode. Ne jamais supprimer une ligne : le registre est l'historique
     qui garantit l'unicité. Ajouter en bas, en conservant l'ordre chronologique. -->
