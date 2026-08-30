# XAUUSD — range de fin de session US, deblayage a l'ouverture asiatique

Test d'une hypothese de marche. Backtest et statistiques uniquement : aucun code
d'execution, aucune connexion broker, aucune recommandation dans les sorties.

## Etat

Le pipeline est complet et teste. **Les donnees n'ont pas pu etre telechargees
depuis cet environnement** : `dukascopy.com` (tous sous-domaines, dont
`datafeed.dukascopy.com`) est refuse par la politique de sortie reseau de la
session — le proxy repond `403` au `CONNECT`. Aucune source de repli n'a ete
substituee : sans le ask reel, le test n'a pas de sens.

La chaine est prevue pour tourner sur la machine de l'utilisateur (macOS, zsh),
ou l'acces au feed est libre.

## Lancer

```zsh
./run.sh test        # tests unitaires + auto-test bout en bout (donnees synthetiques)
./run.sh all         # telechargement 18 mois, agregation, sessions, rapport
```

Ou, par etape :

```zsh
./run.sh download --months 18   # ~13 000 requetes horaires, prefixe par caffeinate -di
./run.sh aggregate              # ticks -> M5 avec spread
./run.sh sessions               # sessions retenues/ecartees + repartition des classes
./run.sh report                 # les 4 mesures, out/report.md, out/plots/
```

Aucune cle d'API n'est necessaire : le feed Dukascopy est public. `.env.local`
est cree vide et ignore par git, au cas ou une cle deviendrait necessaire.

## Ce que fait la chaine

| etape | entree | sortie |
| --- | --- | --- |
| `download` | Dukascopy `.bi5` horaire, bid **et** ask | `data/raw/YYYY-MM.parquet` + manifeste |
| `aggregate` | ticks | `data/m5/YYYY-MM.parquet` (OHLC bid + spread) |
| `sessions` | M5 | `out/sessions.csv`, `data/excluded.csv` |
| `report` | sessions | `out/report.md`, `out/plots/` |

Le telechargement est **reprenable** : un mois deja complet est saute, un mois
incomplet est refait. Le manifeste garde le statut de chaque heure.

## Points de construction

- **Les bougies M5 sont posees sur la grille UTC**, jamais sur l'horloge serveur
  du fournisseur. L'OHLC est construit sur le **bid**.
- **Le spread est une colonne de premier plan** : `spread_mean_pts`,
  `spread_max_pts`, `spread_p95_pts` et le spread horodate de la cloture de
  chaque bougie. Le cout d'execution d'un trade est pris sur **sa** bougie
  d'entree — aucun spread moyen global n'est utilise nulle part.
- **Le ask est obligatoire.** `validate_ticks()` leve `AskMissingError` si le
  flux ne porte pas d'ask exploitable, et `PriceScaleError` si le prix decode
  sort de la plage plausible. Aucune valeur n'est substituee, aucun trou n'est
  interpole.
- **Les deux ancrages tournent sur exactement le meme echantillon** : une date
  n'est gardee que si les deux ancrages la retiennent. Les sessions perdues par
  cette intersection sont journalisees avec le motif
  `ecartee_sur_l_autre_ancrage`.
- **L'ordre de deux franchissements dans une meme bougie M5 est tranche
  exactement**, pas par heuristique : l'agregation conserve `t_high` et `t_low`,
  l'horodatage tick de chaque extreme.

## Exclusions

Journalisees une par une dans `data/excluded.csv` avec leur motif :

| motif | regle |
| --- | --- |
| `week_end` | la session chevauche la fermeture hebdomadaire (ven 21:00 → dim 22:00 UTC) |
| `jour_ferie` | jour ferie US ou chinois sur une des dates de la session |
| `range_sans_donnee` | aucune bougie dans le range de reference |
| `trou_range` | trou de donnees > 15 min dans le range de reference |
| `fenetre_sans_donnee` | aucune bougie dans la fenetre |
| `range_nul` | High == Low |
| `ecartee_sur_l_autre_ancrage` | retenue ici, ecartee sur l'autre ancrage |

## Parametres

Tout est dans `src/grs/constants.py`, une valeur par decision :

- `PROJECTION_FACTOR = 1.0` — passer a `0.5` ne demande que ce changement
- `SWEEP_MAX_BARS = 3`, `BREAKOUT_CONFIRM_BARS = 3`
- `MAX_RANGE_GAP_MIN = 15`, `HISTORY_MONTHS = 18`, `MIN_SESSIONS = 120`
- `BREAKOUT_STOP_BUFFER_R = 0.10` — **hypothese ajoutee**, voir ci-dessous
- criteres d'abandon : `ABANDON_*`

### Hypothese ajoutee

Le cahier des charges dit, pour un BREAKOUT, « stop de l'autre cote de la
borne », sans distance. L'entree se faisant **sur** la borne (au retest), une
distance nulle serait degeneree. Le stop est donc place a
`BREAKOUT_STOP_BUFFER_R` (0.10 R par defaut) de l'autre cote de la borne. Ce
choix pilote directement l'esperance des deux classes BREAKOUT ; il est signale
comme hypothese dans `out/report.md`.

## Tests

`tests/test_classify.py` — 31 assertions sur des cas fabriques a la main :
chaque classe, le franchissement tardif non confirmable, le double cote, les
deux bornes franchies dans la meme bougie, les niveaux de trade, la regle des
15 minutes, la fermeture hebdomadaire.

`tests/selftest.py` — chaine complete sur des ticks **synthetiques**, dans un
repertoire jetable. Prouve que la plomberie tourne ; ne produit aucun resultat
de marche.
