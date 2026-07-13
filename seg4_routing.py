#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Routage seg4 v4 (saison 2) + tolérance des métadonnées. Source UNIQUE, importée par
autoprod.py ET build_episode.py — le routage ne s'infère jamais deux fois de deux façons.

Schéma v4 (ep29+) — chaque épisode porte :
  "ltti_target": "SIRD"        # un des 16 codes LTTI      — MÉTADONNÉE (tolérée, loggée)
  "taxonomy": "miroir"         # taxonomie éditoriale       — MÉTADONNÉE (tolérée, loggée)
  "registre": "psycho"         # registre éditorial         — MÉTADONNÉE (tolérée, loggée)
  "hook_cell": {variable, regard, temps, valence}          — MÉTADONNÉE (tolérée, loggée)
  "seg4_type": "prop"|"narratif"|"champ"                   — ROUTAGE (obligatoire en s2)

Règles :
- Les métadonnées ne bloquent JAMAIS la fabrication (validation douce -> warning, pas d'erreur).
- seg4_type est LA source du routage seg4. Doctrine v2 (HyperFrames-first) : à l'écriture on vise
  "prop" par défaut, "narratif" est l'exception à justifier — mais le code ne devine rien, il lit
  le champ explicite.
- SAISON 2 (ep >= 29) : seg4_type ABSENT ou INVALIDE -> échec franc (fail loud).
- RÉTROCOMPAT (ep02-28, pas de champ) : inférence legacy identique à l'ancien comportement.
"""

SEG4_TYPES = ("prop", "narratif", "champ")

LTTI_CODES = {
    "SIRD", "SITD", "SIRX", "SITX", "OIRD", "OITD", "OIRX", "OITX",
    "SERD", "SETD", "SERX", "SETX", "OERD", "OETD", "OERX", "OETX",
}
HOOK_CELL_KEYS = {"variable", "regard", "temps", "valence"}

SEASON2_MIN = 29                       # ep >= 29 => saison 2 => seg4_type obligatoire
LEGACY_CHAMP = {1, 2, 3, 13}           # ep1 (EP01) + destruction de masse s1
LEGACY_PROP = {4, 5, 7, 9, 10, 15, 17, 19, 22, 24, 25}


class Seg4Error(ValueError):
    """seg4_type absent/invalide sur un épisode qui l'exige."""


def _legacy_type(n):
    if n in LEGACY_CHAMP:
        return "champ"
    if n in LEGACY_PROP:
        return "prop"
    return "narratif"


def _read_seg4_type(episode):
    """seg4_type peut vivre au niveau ÉPISODE (brief prépa) ou sur le SEGMENT 4 (JSON pilotes).
    On lit les deux ; si les deux sont présents et divergent, c'est une erreur de données."""
    ep_lvl = episode.get("seg4_type")
    seg4 = next((s for s in episode.get("segments", []) if s.get("segment") == 4), None)
    seg_lvl = seg4.get("seg4_type") if seg4 else None
    if ep_lvl is not None and seg_lvl is not None and ep_lvl != seg_lvl:
        raise Seg4Error(f"seg4_type contradictoire : épisode={ep_lvl!r} vs segment4={seg_lvl!r}.")
    return seg_lvl if seg_lvl is not None else ep_lvl


def resolve_seg4_type(episode, n):
    """Renvoie 'prop' | 'narratif' | 'champ'. Fail loud si s2 sans seg4_type valide."""
    raw = _read_seg4_type(episode)
    if raw is not None:
        if raw not in SEG4_TYPES:
            raise Seg4Error(
                f"ep{n}: seg4_type invalide {raw!r} — attendu l'un de {SEG4_TYPES}.")
        return raw
    if n >= SEASON2_MIN:
        raise Seg4Error(
            f"ep{n}: seg4_type ABSENT — obligatoire pour la saison 2 (ep>={SEASON2_MIN}). "
            f"Ajoute \"seg4_type\": \"prop\"|\"narratif\"|\"champ\" dans le JSON.")
    return _legacy_type(n)


def log_s2_metadata(episode, n):
    """Métadonnées v4 : loggées et validées en douceur (warning), JAMAIS bloquantes."""
    present = {k: episode[k] for k in ("ltti_target", "taxonomy", "registre", "hook_cell") if k in episode}
    if not present:
        return
    lt = episode.get("ltti_target")
    if lt is not None and lt not in LTTI_CODES:
        print(f"[meta] ep{n}: ltti_target {lt!r} hors des 16 codes LTTI (toléré).", flush=True)
    hc = episode.get("hook_cell")
    if isinstance(hc, dict) and set(hc) != HOOK_CELL_KEYS:
        print(f"[meta] ep{n}: hook_cell clés {sorted(hc)} != {sorted(HOOK_CELL_KEYS)} (toléré).",
              flush=True)
    print(f"[meta] ep{n}: {present}", flush=True)


if __name__ == "__main__":
    # Auto-test rapide du contrat de données.
    assert resolve_seg4_type({}, 2) == "champ"
    assert resolve_seg4_type({}, 5) == "prop"
    assert resolve_seg4_type({}, 6) == "narratif"
    assert resolve_seg4_type({"seg4_type": "prop"}, 30) == "prop"
    assert resolve_seg4_type({"seg4_type": "narratif"}, 29) == "narratif"
    for bad in ({}, {"seg4_type": "prose"}):
        try:
            resolve_seg4_type(bad, 29); raise SystemExit("FAIL: aurait dû lever")
        except Seg4Error:
            pass
    log_s2_metadata({"ltti_target": "SIRD", "taxonomy": "miroir",
                     "hook_cell": {"variable": "nightmare", "regard": "ennemi",
                                   "temps": "present", "valence": "++"}}, 29)
    print("seg4_routing : auto-test OK")
