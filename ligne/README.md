# Publisher LIGNE — la file

Publie les épisodes **LIGNE** sur **@kongrave_** depuis une simple file d'attente.
Aucun planning à tenir : tu déposes, le cron publie le plus ancien, un par jour.

## Ton seul geste : déposer

Un épisode validé PO = **un dossier** dans `ligne/queue/` contenant :

- **un** fichier `.mp4` (le master final, avec filigrane),
- un fichier `caption.txt` (la légende Instagram, texte brut).

```
ligne/queue/
  L01/
    L1.mp4
    caption.txt
  L02/
    L2.mp4
    caption.txt
```

Puis `git add ligne/queue && git commit && git push`. C'est tout.

**Nom du dossier = ordre de publication.** Le plus ancien = celui dont le nom
**trie en premier**. Utilise donc un préfixe qui trie : `L01`, `L02`, … (zéro
devant) ou une date `2026-07-16_L1`. (On n'utilise pas la date du fichier :
un `git checkout` la réécrit sur le runner.)

## Ce que fait le cron (chaque jour, 18h30 Paris)

1. Prend le **plus ancien** dossier de `ligne/queue/`.
2. Le publie sur @kongrave_ (Graph API, mêmes secrets que la saga).
3. Le déplace dans `ligne/published/` et journalise dans `ligne/publish_log.json`.
4. **File vide → il ne publie RIEN et te notifie** (Telegram). Jamais de bruit
   de remplissage.

## Garde-fous

- **Cadence.** `ligne/config.json` → `cadence_hours` (défaut **24**). Le workflow
  **refuse de publier** si le dernier post Ligne date de **moins de** `cadence_hours`,
  même si la file est pleine. Impossible de spammer, même par erreur de dépôt.
  Pour accélérer un jour (24 → 12 → 6), change **ce seul chiffre**. Rien d'autre.
- **Fenêtre horaire.** Publie à **18h30 Paris** toute l'année (deux crons UTC
  couvrent été/hiver ; le script filtre sur l'heure de Paris).

## Vérifier / publier à la main

Repo GitHub → **Actions → LIGNE auto-publish → Run workflow** :

- `dry_run: true` → crée le conteneur Meta **sans publier ni déplacer** (test).
- `force: true` → ignore la fenêtre horaire et la cadence (publication immédiate).

En local (si `.env.local` présent avec le token) :

```bash
python publish_ligne.py --dry-run --force   # teste sans publier
python publish_ligne.py --force             # publie le plus ancien tout de suite
```
