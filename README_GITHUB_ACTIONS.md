# KONGRAVE Publisher — déploiement GitHub Actions (100 % gratuit)

Remplace le VPS. GitHub exécute le publieur toutes les heures, gratuitement, et publie
les Reels aux dates prévues dans `schedule.json`. Aucun serveur, aucune carte bancaire.

## Pourquoi ça marche sans hébergement vidéo

`ig_api.py` envoie les octets du fichier **local** à Meta (upload resumable). Les MP4
vivent donc **dans le repo** ; le runner GitHub les a sous la main au moment de publier.

---

## Mise en place (une seule fois, ~10 min)

### 1. Créer le dépôt (privé)
1. github.com → **New repository** → nom `kongrave-publisher` → **Private** → *Create*.
2. Sur le Mac, dans `~/disruptive-reels-pipeline/publisher/` :
   ```bash
   git init
   git add .
   git commit -m "Publieur KONGRAVE — GitHub Actions"
   git branch -M main
   git remote add origin https://github.com/<TON_COMPTE>/kongrave-publisher.git
   git push -u origin main
   ```
   > `.env.local` n'est jamais poussé (il est dans `.gitignore`). Le token n'ira **que**
   > dans les Secrets GitHub (étape 3).

### 2. Poser les vidéos + le planning
- Mets les `.mp4` finis dans `inbox/` (ex. `inbox/EPISODE_01_kongrave.mp4`).
- Renseigne `schedule.json` : pour chaque épisode, `filepath`, `caption`,
  `publish_datetime` (avec le fuseau, ex. `2026-07-09T18:00:00+02:00`).
- Commit + push :
  ```bash
  git add inbox/ schedule.json
  git commit -m "ep02 prêt + planning"
  git push
  ```

### 3. Déposer les secrets (le token, jamais dans un fichier)
Repo → **Settings → Secrets and variables → Actions → New repository secret**. Crée :

| Nom | Valeur |
|---|---|
| `META_ACCESS_TOKEN` | le token de Page permanent (Toastfx) |
| `INSTAGRAM_BUSINESS_ACCOUNT_ID` | `17841416734985479` |
| `TELEGRAM_BOT_TOKEN` | *(optionnel — notifications)* |
| `TELEGRAM_CHAT_ID` | *(optionnel)* |

### 4. Vérifier sans rien publier (dry-run)
Repo → onglet **Actions** → workflow **KONGRAVE auto-publish** → **Run workflow** →
coche **dry_run = true** → *Run*. Le job crée le conteneur et va jusqu'à `FINISHED`
**sans publier**. Si c'est vert, tout est câblé.

### 5. Laisser tourner
Rien à faire. Le cron horaire publie chaque épisode dès que sa date est atteinte, une
seule fois (idempotence via `output/publish_log.json`, committé automatiquement).

---

## Au quotidien
- Nouvel épisode : `git add inbox/EPISODE_0X.mp4 schedule.json && git commit && git push`.
- Suivi : onglet **Actions** (chaque run) + notifications Telegram si configurées.
- Journal : `output/publish_log.json` (committé par le bot après chaque publication).

## Bon à savoir (limites GitHub)
- **Ponctualité** : le cron GitHub peut être **retardé de 5–30 min** (pire à l'heure
  pile). Un post prévu 18:00 part entre ~18:07 et ~18:40. Pour du plus serré → me
  demander la variante **GitHub Releases** (runs quasi gratuits, cron toutes les 15 min).
- **Budget** : ~1080 min/mois utilisées sur 2000 gratuites. Large.
- **Inactivité 60 j** : GitHub désactive les workflows planifiés si le repo n'a **aucun
  commit pendant 60 jours**. Nos publications committent le journal → activité maintenue.
  Après la fin de la saison, un simple `git commit --allow-empty` réveille le cron.
- **Garder le repo léger** : tu peux supprimer du repo les MP4 déjà publiés
  (`git rm inbox/EPISODE_0X.mp4`) — le journal garde la trace, ils ne seront pas republiés.

## Sécurité
- Le token n'existe que dans **GitHub Secrets** (chiffré) — jamais dans le code, jamais
  dans un commit. `.env.local` reste local et ignoré par git.
- Repo **privé** : les vidéos non encore publiées ne sont pas exposées.
