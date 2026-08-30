#!/usr/bin/env python3
"""cta_follows.py — combien d'abonnés chaque Reel a-t-il rapporté ?

Lecture seule. Répond à une question précise : la position du CTA change-t-elle
le nombre d'abonnements gagnés par post ? Le régime a basculé à L72 — avant, le
CTA ouvrait la légende avec un mot-clé ; depuis, la légende se termine par
« Follow @kongrave_ ».

Le rapprochement média <-> épisode se fait par le journal ligne/publish_log.json,
qui garde le media_id rendu par Meta à chaque publication. La métrique demandée
est `follows`, disponible au niveau du média pour un compte professionnel ; si
l'API la refuse, le script le dit au lieu d'inventer un chiffre.

Sortie : une ligne par épisode, puis les deux moyennes.

  python3 ligne/cta_follows.py [nombre_de_medias]
"""

import json
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import ig_api  # noqa: E402  (le chemin doit être posé avant l'import)

LIGNE_DIR = pathlib.Path(__file__).resolve().parent
LOG_PATH = LIGNE_DIR / "publish_log.json"

BASCULE = 72          # L72 = premier épisode avec le CTA en fin de légende
METRIQUES = "follows,reach,views,total_interactions"


def journal():
    """{media_id: nom d'épisode} pour toutes les publications réussies."""
    try:
        entrees = json.loads(LOG_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    par_media = {}
    for e in entrees:
        if e.get("status") != "success":
            continue
        mid = str(e.get("media_id") or "").strip()
        nom = str(e.get("episode") or e.get("name") or "").strip()
        if mid and nom:
            par_media[mid] = nom
    return par_media


def insights(media_id):
    """Renvoie {metrique: valeur} ou {'_erreur': texte} — jamais d'exception."""
    import requests
    url = f"{ig_api.GRAPH_HOST}/{ig_api.GRAPH_VERSION}/{media_id}/insights"
    try:
        resp = requests.get(url, params={"metric": METRIQUES,
                                         "access_token": ig_api._access_token()},
                            timeout=30)
        data = resp.json()
    except Exception as exc:                                   # noqa: BLE001
        return {"_erreur": f"{type(exc).__name__}: {exc}"}
    if "error" in data:
        return {"_erreur": data["error"].get("message", "erreur API")}
    out = {}
    for bloc in data.get("data", []):
        valeurs = bloc.get("values") or [{}]
        out[bloc.get("name")] = valeurs[0].get("value")
    return out


def numero(nom):
    chiffres = "".join(c for c in nom if c.isdigit())
    return int(chiffres) if chiffres else None


def main():
    combien = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    par_media = journal()
    medias = ig_api.list_recent_media(limit=combien)
    print(f"[cta] {len(medias)} médias remontés, {len(par_media)} publications au journal\n")
    print(f"  {'épisode':<9}{'CTA':<10}{'abonnés':>8}{'portée':>9}{'vues':>9}  date")

    avant, apres = [], []
    for m in medias:
        nom = par_media.get(str(m.get("id")))
        if not nom:
            continue
        n = numero(nom)
        if n is None:
            continue
        regime = "fin" if n >= BASCULE else "début"
        mesure = insights(m["id"])
        if "_erreur" in mesure:
            print(f"  {nom:<9}{regime:<10}{'—':>8}{'—':>9}{'—':>9}  {mesure['_erreur'][:60]}")
            continue
        f = mesure.get("follows")
        r = mesure.get("reach")
        v = mesure.get("views")
        print(f"  {nom:<9}{regime:<10}{str(f if f is not None else '—'):>8}"
              f"{str(r if r is not None else '—'):>9}{str(v if v is not None else '—'):>9}"
              f"  {(m.get('timestamp') or '')[:10]}")
        if isinstance(f, (int, float)):
            (apres if n >= BASCULE else avant).append((f, r or 0, v or 0))

    print()
    for etiquette, lot in (("CTA en début de légende (avant L72)", avant),
                           ("CTA en fin de légende (L72 et après)", apres)):
        if not lot:
            print(f"  {etiquette} : aucune donnée exploitable.")
            continue
        n = len(lot)
        moy = sum(x[0] for x in lot) / n
        vues = sum(x[2] for x in lot)
        abos = sum(x[0] for x in lot)
        taux = (abos / vues * 100) if vues else 0
        print(f"  {etiquette} : {n} posts, {abos:.0f} abonnés au total, "
              f"{moy:.1f} par post, {taux:.2f} % des vues.")


if __name__ == "__main__":
    if not os.getenv("META_ACCESS_TOKEN"):
        print("[cta] META_ACCESS_TOKEN absent — ce script ne tourne qu'en CI.")
        sys.exit(0)
    main()
