#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Chargeur UNIQUE des épisodes KONGRAVE — source de vérité de « quels épisodes existent ».

Fusionne :
  - la saison 1 (`KONGRAVE_episodes_02_to_28_v3.json`, ou l'override `KONGRAVE_JSON`),
  - la saison 2 (`KONGRAVE_saison2.json`) si le fichier est présent.

La saison 1 (canon validé) reste figée et séparée ; la saison 2 (schéma v4) est un fichier à part.
La fusion trie par `number`, donc la file et la cadence enchaînent ep28 -> ep29 sans trou.
En cas de doublon de numéro, la saison 2 l'emporte (permet un correctif ciblé sans toucher v3).
"""
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
S1_JSON = Path(os.environ.get("KONGRAVE_JSON") or ROOT / "KONGRAVE_episodes_02_to_28_v3.json")
S2_JSON = ROOT / "KONGRAVE_saison2.json"


def _read(path):
    return json.load(open(path))["episodes"]


def load_all():
    """Liste des épisodes s1 + s2 fusionnés, triée par number."""
    eps = {}
    for e in _read(S1_JSON):
        eps[e["number"]] = e
    if S2_JSON.exists():
        for e in _read(S2_JSON):
            eps[e["number"]] = e
    return [eps[n] for n in sorted(eps)]


def by_number():
    """Dict {number: episode} des épisodes s1 + s2."""
    return {e["number"]: e for e in load_all()}


if __name__ == "__main__":
    eps = load_all()
    nums = [e["number"] for e in eps]
    print(f"kongrave_episodes : {len(eps)} épisodes  (s1={S1_JSON.name}"
          f"{', s2=' + S2_JSON.name if S2_JSON.exists() else ', pas de saison2'})")
    print(f"  numéros : {nums[:5]}…{nums[-3:] if len(nums) > 8 else ''}")
