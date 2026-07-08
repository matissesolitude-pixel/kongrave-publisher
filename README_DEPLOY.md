# KONGRAVE Publisher — déploiement VPS

Auto-publication des Reels Instagram KONGRAVE via l'API Graph.
Le **Mac produit** les épisodes et les pousse ; le **VPS publie** tout seul, 24/7.

```
Mac (production)                 VPS Linux (24/7)
build_episode.py → .mp4          cron */5 → cron_publisher.py
      │  sync.sh (rsync)                │
      └──────────────────►  ~/kongrave-publisher/
                              inbox/*.mp4 · schedule.json · .env.local
                              ig_api.py · publish_reel.py · cron_publisher.py · notify.py
                              output/publish_log.json
```

> ⚠️ **L'API Graph ne programme pas les Reels** (publication immédiate uniquement).
> C'est notre cron sur le VPS qui joue le rôle de planificateur : il publie un épisode
> quand son `publish_datetime` est dépassé.

---

## 1. Modules

| Fichier | Rôle |
|---|---|
| `ig_api.py` | Client bas niveau Graph API : container (resumable upload), statut, publish. Retry 3×. |
| `publish_reel.py` | Publie **un** épisode : container → attend `FINISHED` → publish. `--dry-run` sûr. |
| `cron_publisher.py` | Lancé par cron : lit `schedule.json`, publie les épisodes dus, journalise, notifie. |
| `notify.py` | Notification Telegram (succès/échec). |
| `sync.sh` | Sur le Mac : `rsync` des `.mp4` + `schedule.json` vers le VPS. |
| `schedule.example.json` | Gabarit de planning (copier en `schedule.json`). |

---

## 2. Prérequis Meta (à faire une fois)

1. Compte **Instagram Business** relié à une **Page Facebook** (via l'app Instagram → Paramètres → Compte pro).
2. Dans **Meta Business Manager** :
   - Récupérer l'**`INSTAGRAM_BUSINESS_ACCOUNT_ID`**.
   - Créer un **Utilisateur système** → générer un **token longue durée** avec les permissions :
     `instagram_basic`, `instagram_content_publish`, `pages_read_engagement`, `business_management`.
3. **Telegram** : créer un bot via [@BotFather] → récupérer `TELEGRAM_BOT_TOKEN` ;
   récupérer `TELEGRAM_CHAT_ID` (envoyer un message au bot puis lire
   `https://api.telegram.org/bot<TOKEN>/getUpdates`).

---

## 3. Provisioning du VPS

Un petit VPS suffit (DigitalOcean / Hetzner, ~5 €/mois), Debian/Ubuntu.

```bash
# Sur le VPS
sudo apt update && sudo apt install -y python3 python3-pip python3-venv rsync
mkdir -p ~/kongrave-publisher && cd ~/kongrave-publisher
python3 -m venv .venv && . .venv/bin/activate
pip install "requests>=2.31" "python-dotenv>=1.0.1"
```

Copier les modules Python sur le VPS (depuis le Mac, dans `publisher/`) :

```bash
rsync -av --exclude '.env.local' --exclude 'output' --exclude 'inbox/*.mp4' \
  ig_api.py publish_reel.py cron_publisher.py notify.py \
  schedule.example.json README_DEPLOY.md \
  VPS_HOST:~/kongrave-publisher/
```

Créer le fichier secret **directement sur le VPS** (jamais synchronisé) :

```bash
cd ~/kongrave-publisher
cp .env.example .env.local   # ou recréer d'après README
nano .env.local              # coller les vraies valeurs
chmod 600 .env.local
```

---

## 4. Depuis le Mac : produire → planifier → pousser

```bash
cd ~/disruptive-reels-pipeline/publisher
cp schedule.example.json schedule.json    # première fois
# éditer schedule.json : episode_number, filepath (inbox/…), caption, publish_datetime
cp ../output/v3/EPISODE_01_kongrave.mp4 inbox/

VPS_HOST=deploy@203.0.113.10 ./sync.sh    # pousse inbox/*.mp4 + schedule.json
```

`publish_datetime` est une date ISO (`2026-07-07T18:00:00+02:00`). Une date sans fuseau
est interprétée en heure locale du VPS.

---

## 5. Test sûr (AVANT toute publication visible)

Le mode `--dry-run` va jusqu'au conteneur `FINISHED` **sans** appeler `media_publish` :
rien n'apparaît sur le compte.

```bash
# Sur le VPS, dans ~/kongrave-publisher, venv activé :
python3 publish_reel.py inbox/EPISODE_01_kongrave.mp4 "Test KONGRAVE" --dry-run
# Attendu : [DRY-RUN OK] Conteneur prêt (FINISHED) : <id>

python3 notify.py "Test notif KONGRAVE ✅"   # vérifie Telegram
```

**⛔ STOP ici.** Ne retire `--dry-run` (ou n'active le cron) qu'après validation explicite.

---

## 6. Activer le cron (une fois validé)

```bash
crontab -e
# Ajouter (adapter le chemin du venv) :
*/5 * * * * cd ~/kongrave-publisher && ~/kongrave-publisher/.venv/bin/python3 cron_publisher.py >> output/cron.out 2>&1
```

Le publieur tourne toutes les 5 min :
- publie les épisodes dont l'heure est passée et qui ne sont pas déjà publiés ;
- écrit chaque résultat dans `output/publish_log.json` (idempotent) ;
- notifie sur Telegram ;
- respecte la limite de 50 publications / 24 h ;
- ne se chevauche jamais (verrou `fcntl`).

Pour un cycle « à blanc » sans rien publier : `python3 cron_publisher.py --dry-run`.

---

## 7. Sécurité

- `META_ACCESS_TOKEN` vit **uniquement** dans `.env.local` sur le VPS (`chmod 600`),
  jamais dans le code, jamais committé, jamais synchronisé par `sync.sh`.
- Un conteneur `EXPIRED` ou `ERROR` n'est **jamais** publié.
- Le token System User est longue durée : le renouveler avant expiration (surveiller
  les erreurs `HTTP 190` dans les notifications).
