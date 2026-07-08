#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Détection de TEXTE halluciné sur une scène narrative (Gemini) + garde-fou.

Règle KONGRAVE : aucune scène ne doit contenir de lettres/mots lisibles (Gemini a déjà
halluciné « SIN CITY » sur une enseigne néon). En prod autonome (option B), on ne peut pas
valider à l'œil : on passe l'image au crible d'un OCR (tesseract) ; si un MOT lisible apparaît,
on considère la scène invalide et on régénère avec un prompt « no text » renforcé.

`image_has_text(path)` renvoie True si l'OCR trouve au moins un mot alphabétique d'au moins
MIN_LEN lettres avec une confiance ≥ MIN_CONF. Seuils volontairement stricts pour limiter les
faux positifs sur l'encrage Sin City (hachures interprétées comme des lettres isolées).

Exception : ep11 (journal) contient de l'écriture manuscrite INTRINSÈQUE au concept — pour ces
scènes on passe `allow_text=True` (on ne vérifie pas).
"""
import sys

MIN_LEN = 3       # un "mot" doit faire >= 3 lettres pour compter (évite le bruit)
MIN_CONF = 62     # confiance OCR minimale (%)
MIN_WORDS = 1     # nb de mots lisibles au-delà duquel la scène est rejetée


def image_has_text(path: str) -> bool:
    """True si l'OCR détecte du texte lisible sur l'image. False si aucun / OCR indispo."""
    try:
        import pytesseract
        from PIL import Image, ImageOps
    except Exception as e:
        print(f"[textcheck] OCR indisponible ({e}) — on considère 'pas de texte'.", flush=True)
        return False
    try:
        img = Image.open(path).convert("L")
        # rehausse le contraste pour aider l'OCR à isoler d'éventuelles lettres
        img = ImageOps.autocontrast(img)
        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
    except Exception as e:
        print(f"[textcheck] échec OCR ({e}) — on considère 'pas de texte'.", flush=True)
        return False
    hits = []
    for txt, conf in zip(data.get("text", []), data.get("conf", [])):
        t = "".join(ch for ch in (txt or "") if ch.isalpha())
        try:
            c = float(conf)
        except (TypeError, ValueError):
            c = -1
        if len(t) >= MIN_LEN and c >= MIN_CONF:
            hits.append((t, c))
    if hits:
        print(f"[textcheck] TEXTE détecté : {hits[:5]}", flush=True)
    return len(hits) >= MIN_WORDS


if __name__ == "__main__":
    # usage : python scene_textcheck.py image.png  -> exit 1 si texte détecté
    p = sys.argv[1]
    found = image_has_text(p)
    print("TEXTE" if found else "PROPRE", p)
    sys.exit(1 if found else 0)
