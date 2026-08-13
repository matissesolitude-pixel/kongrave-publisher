#!/usr/bin/env python3
"""
LIGNE — publications.py — LA LISTE ÉCRITE.

Génère `ligne/PUBLICATIONS.md` : l'état des publications sous une forme lisible —
ce qui est passé, ce qui a été refusé, et où on en est.

POURQUOI ELLE EXISTE. Les masters `.mp4` ne sont plus conservés (3,3 Go pour des
fichiers déjà en ligne). Ce qui doit survivre à leur suppression, c'est la TRACE :
quel épisode est publié, quand, sous quel `media_id`, lesquels Meta a refusés et
combien de fois. Sans cette liste, supprimer les dossiers reviendrait à perdre
l'historique de publication.

Les sources sont déjà dans le dépôt, elles étaient juste illisibles :
  · `publish_log.json`     — le journal (succès et échecs horodatés) ;
  · `_hold/`               — les épisodes écartés, avec le motif dans leur nom ;
  · `engine/*.refused_*`   — les moteurs archivés après refus Meta ;
  · `publish_state.json`   — le compteur d'échecs en cours ;
  · `queue/`               — ce qui attend d'être publié.

USAGE
  python3 ligne/publications.py            # régénère PUBLICATIONS.md
  python3 ligne/publications.py --verifie  # sort 1 si le fichier n'est pas à jour
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import re
import sys

LIGNE = pathlib.Path(__file__).resolve().parent
SORTIE = LIGNE / "PUBLICATIONS.md"


def _charge(nom, defaut):
    p = LIGNE / nom
    if not p.is_file():
        return defaut
    try:
        return json.loads(p.read_text()) or defaut
    except Exception:
        return defaut


def _jour(iso: str) -> str:
    return (iso or "")[:10] or "?"


def construire() -> str:
    log = _charge("publish_log.json", [])
    etat = _charge("publish_state.json", {})

    succes, echecs = {}, collections.Counter()
    motifs = {}
    for e in log:
        if not isinstance(e, dict):
            continue
        ep = e.get("episode")
        if not ep:
            continue
        if e.get("status") == "success":
            succes[ep] = e
        else:
            echecs[ep] += 1
            err = (e.get("error") or "").strip()
            if "ProcessingFailedError" in err:
                motifs[ep] = "refus Meta (ProcessingFailedError)"
            elif err:
                motifs[ep] = err.split("\n")[0][:70]

    hold = sorted(p.name for p in (LIGNE / "_hold").iterdir()) if (LIGNE / "_hold").is_dir() else []
    refused = sorted(p.name for p in (LIGNE / "engine").glob("*.refused_*")) \
        if (LIGNE / "engine").is_dir() else []
    queue = sorted(p.name for p in (LIGNE / "queue").iterdir()
                   if p.is_dir()) if (LIGNE / "queue").is_dir() else []

    ordre = sorted(succes, key=lambda k: (succes[k].get("published_at") or ""))
    dernier = ordre[-1] if ordre else None
    nums = [int(m.group(1)) for k in succes if (m := re.match(r"L0*(\d+)$", k))]
    prochain = f"L{max(nums) + 1:02d}" if nums else "L01"

    L = ["# PUBLICATIONS — LA LIGNE", "",
         "> Généré par `ligne/publications.py`. **Ne pas éditer à la main.**",
         "> Cette liste est la trace qui remplace les masters `.mp4` : eux sont déjà en",
         "> ligne sur Instagram, elle seule dit ce qui est passé et ce qui a été refusé.",
         "", "## OÙ ON EN EST", ""]
    if dernier:
        d = succes[dernier]
        L += [f"- **Dernier publié : {dernier}**, le {_jour(d.get('published_at'))} "
              f"(`media_id` {d.get('media_id', '?')})"]
    L += [f"- Épisodes publiés : **{len(succes)}**",
          f"- Prochain numéro attendu : **{prochain}**",
          f"- En file d'attente : **{len(queue)}**" + (f" ({', '.join(queue)})" if queue else ""),
          f"- Écartés dans `_hold/` : **{len(hold)}**",
          f"- Moteurs archivés après refus : **{len(refused)}**",
          f"- Compteur d'échecs en cours : "
          + (", ".join(f"{k} ({v})" for k, v in etat.items()) if etat else "aucun"),
          "", f"## PUBLIÉS ({len(succes)})", "",
          "| Épisode | Publié le | media_id | Tentatives avant succès |",
          "|---|---|---|---|"]
    for ep in ordre:
        d = succes[ep]
        n = echecs.get(ep, 0)
        L.append(f"| {ep} | {_jour(d.get('published_at'))} | `{d.get('media_id', '?')}` | "
                 f"{n if n else '—'} |")

    rates = sorted(set(echecs) - set(succes))
    L += ["", f"## JAMAIS PUBLIÉS ({len(rates)})", ""]
    if rates:
        L += ["| Épisode | Échecs | Dernier motif |", "|---|---|---|"]
        L += [f"| {ep} | {echecs[ep]} | {motifs.get(ep, '?')} |" for ep in rates]
    else:
        L.append("Aucun : tout épisode entré en file a fini par passer.")

    peines = [(ep, echecs[ep]) for ep in ordre if echecs.get(ep, 0) >= 3]
    L += ["", "## PASSÉS DANS LA DOULEUR (3 refus ou plus avant succès)", ""]
    L += ([f"- **{ep}** — {n} refus, puis publié" for ep, n in peines] if peines
          else ["Aucun."])

    L += ["", f"## ÉCARTÉS — `_hold/` ({len(hold)})", "",
          "Le nom porte le motif : `_meta_` = refus Meta, `_texte_coupe` / `_badlabels` = "
          "défaut d'étiquettes, `_repro_` = reproduction programmée.", ""]
    L += [f"- `{h}`" for h in hold] or ["Aucun."]

    L += ["", f"## MOTEURS ARCHIVÉS APRÈS REFUS ({len(refused)})", "",
          "Conservés volontairement : c'est l'historique des refus, et la consigne est de "
          "ne jamais recoder à l'identique un flux que Meta a rejeté.", ""]
    L += [f"- `{r}`" for r in refused] or ["Aucun."]
    return "\n".join(L) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description="Génère la liste écrite des publications.")
    ap.add_argument("--verifie", action="store_true",
                    help="sort 1 si PUBLICATIONS.md n'est pas à jour (pour la CI)")
    a = ap.parse_args()
    txt = construire()
    if a.verifie:
        actuel = SORTIE.read_text() if SORTIE.is_file() else ""
        if actuel != txt:
            sys.exit("PUBLICATIONS.md n'est pas à jour — lancer python3 ligne/publications.py")
        print("PUBLICATIONS.md à jour.")
        return
    SORTIE.write_text(txt)
    print(f"→ {SORTIE} ({len(txt.splitlines())} lignes)")


if __name__ == "__main__":
    main()
