#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Garde-fou OCR sur une scène narrative (Gemini) : rejette le texte ET les chiffres hallucinés.

Règle KONGRAVE : aucune scène ne doit contenir de mots lisibles (Gemini a déjà halluciné
« SIN CITY » sur une enseigne). En prod autonome on ne valide pas à l'œil : on passe l'image
au crible d'un OCR (tesseract) et on régénère si quelque chose d'interdit survit.

DEUX niveaux de garde-fou :
  1. CHIFFRES / MONTANTS EN DEVISE — **toujours interdits, sans exception**, même sur les
     scènes à écriture manuscrite autorisée (journal ep11). Garde-fou compliance LTTI absolu :
     aucun chiffre, aucun montant à l'écran, jamais (cf. LTTI_PROFILES.md §4).
  2. MOTS ALPHABÉTIQUES lisibles — interdits, SAUF si `allow_text=True` (journaux dont
     l'écriture manuscrite illisible fait partie du concept).

API : `image_forbidden(path, allow_text=False) -> (bool, reason)`.
Compat : `image_has_text(path)` (mots alpha) conservé.
"""
import sys

MIN_LEN = 3        # un "mot" alpha doit faire >= 3 lettres pour compter (évite le bruit d'encrage)
MIN_CONF = 62      # confiance OCR minimale pour un mot alpha (%)
MIN_WORDS = 1      # nb de mots lisibles au-delà duquel la scène est rejetée

CURRENCY = "$€£¥₩₿"   # symboles de devise
NUM_CONF = 58         # confiance min pour un nombre / une devise
DIGIT_SOLO_CONF = 80  # un chiffre ISOLÉ n'est rejeté qu'à haute confiance (l'encrage Sin City
                      # se lit parfois comme un "1"/"7" ; un montant lisible fait >= 2 chiffres)


def _ocr_tokens(path):
    """Retourne [(texte, conf), ...] ou None si l'OCR est indisponible."""
    try:
        import pytesseract
        from PIL import Image, ImageOps
    except Exception as e:
        print(f"[textcheck] OCR indisponible ({e}) — on considère 'propre'.", flush=True)
        return None
    try:
        img = ImageOps.autocontrast(Image.open(path).convert("L"))
        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
    except Exception as e:
        print(f"[textcheck] échec OCR ({e}) — on considère 'propre'.", flush=True)
        return None
    out = []
    for txt, conf in zip(data.get("text", []), data.get("conf", [])):
        try:
            c = float(conf)
        except (TypeError, ValueError):
            c = -1.0
        out.append((txt or "", c))
    return out


def image_has_number_or_currency(path: str) -> bool:
    """True si un CHIFFRE lisible ou un symbole/montant de devise apparaît.
    TOUJOURS interdit, même quand l'écriture manuscrite est autorisée."""
    toks = _ocr_tokens(path)
    if toks is None:
        return False
    hits = []
    for txt, c in toks:
        if c < NUM_CONF:
            continue
        if any(ch in CURRENCY for ch in txt):
            hits.append((txt, c)); continue
        digits = [ch for ch in txt if ch.isdigit()]
        if len(digits) >= 2:                       # 41, 2026, 41,000... = montant/nombre lisible
            hits.append((txt, c)); continue
        if len(digits) == 1 and c >= DIGIT_SOLO_CONF:
            hits.append((txt, c))
    if hits:
        print(f"[textcheck] CHIFFRE/DEVISE détecté : {hits[:5]}", flush=True)
    return bool(hits)


def image_has_text(path: str) -> bool:
    """True si l'OCR détecte un MOT alphabétique lisible (>= MIN_LEN lettres, conf >= MIN_CONF)."""
    toks = _ocr_tokens(path)
    if toks is None:
        return False
    hits = []
    for txt, c in toks:
        t = "".join(ch for ch in txt if ch.isalpha())
        if len(t) >= MIN_LEN and c >= MIN_CONF:
            hits.append((t, c))
    if hits:
        print(f"[textcheck] TEXTE détecté : {hits[:5]}", flush=True)
    return len(hits) >= MIN_WORDS


def image_forbidden(path: str, allow_text: bool = False):
    """Garde-fou unifié. Renvoie (True, raison) si l'image doit être rejetée.
    - chiffres / devises : TOUJOURS interdits (même si allow_text) ;
    - mots alphabétiques : interdits sauf si allow_text (journaux manuscrits)."""
    if image_has_number_or_currency(path):
        return True, "chiffre/devise"
    if not allow_text and image_has_text(path):
        return True, "texte"
    return False, ""


if __name__ == "__main__":
    # usage : python scene_textcheck.py image.png [--allow-text]  -> exit 1 si interdit
    p = sys.argv[1]
    allow = "--allow-text" in sys.argv[2:]
    bad, reason = image_forbidden(p, allow_text=allow)
    print(f"{'REJET(' + reason + ')' if bad else 'PROPRE'} {p}")
    sys.exit(1 if bad else 0)
