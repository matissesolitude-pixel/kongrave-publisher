#!/usr/bin/env python3
"""
DESSIN — illustrations.py — LA SÉRIE D'EXERCICES PAR MODÈLE D'IMAGE.

Les rigs vectoriels du dossier (`figure.py`, `encre.py`, `athlete.py`) donnent la
cohérence et le contrôle de pose, jamais la qualité d'une illustration. Ici c'est
l'inverse : un modèle d'image donne le trait, et c'est la FEUILLE DE PERSONNAGE qui
rattrape la cohérence.

LA FEUILLE DE PERSONNAGE EST TOUT LE TRAVAIL.
  Le problème d'une série n'est pas de réussir une image, c'est que ce soit LA MÊME
  personne sur les trente. Un modèle d'image dérive dès la troisième si on lui décrit
  le personnage « à peu près » : la coiffure change, la carnation change, la tenue
  change. La parade est un bloc de description FIGÉ, identique octet pour octet à
  chaque appel, où seule la pose varie. C'est le seul champ qu'on touche entre deux
  exercices — tout le reste est constant par construction.

CLÉ : `GEMINI_API_KEY`, résolue comme dans `gen_seg4_narratif.py` — variable
d'environnement d'abord (secret GitHub `GEMINI_API` en CI), `.env.local` en repli.
Elle n'existe PAS dans une session cloud : passer par le workflow
`.github/workflows/dessin-illustrations.yml`, qui tourne là où le secret vit.

USAGE
  python3 dessin/illustrations.py --liste
  python3 dessin/illustrations.py -e squat fente gainage
  python3 dessin/illustrations.py --tout --variantes 2
  python3 dessin/illustrations.py -e squat --ratio 1:1 --out dessin/illustrations
"""
from __future__ import annotations

import argparse
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODEL_IMG = "gemini-3.1-flash-image"        # même modèle que gen_seg4_narratif.py


# ====================================================== LA FEUILLE DE PERSONNAGE
# NE PAS RETOUCHER À LA LÉGÈRE. Chaque mot enlevé est un degré de liberté rendu au
# modèle, donc une dérive possible d'une image à l'autre. Si le personnage doit
# changer, on change ce bloc UNE fois et on régénère TOUTE la série.

PERSONNAGE = (
    "The exact same recurring character in every image: a young athletic woman in her "
    "mid-twenties, lean muscular fitness build with visible defined abs, strong "
    "shoulders and glutes, narrow waist, broad shoulder-to-waist V taper. "
    "Warm tanned skin. Long dark brown hair tied in a high ponytail that swings with "
    "the movement. Confident focused expression, no smile. "
    "Outfit, always identical: a charcoal grey sports bra, high-waisted navy leggings, "
    "white and grey running shoes. "
)

STYLE = (
    "Comic book / cartoon vector illustration. Bold clean black outlines of varying "
    "thickness. Flat cel shading with exactly two tones per material, one light source "
    "from the upper left, crisp shadow edges. Saturated but limited palette. "
    "Confident inked linework, anatomy drawn with interior muscle lines (deltoid, "
    "biceps, abdominals, quadriceps, calves). No gradients, no airbrush, no "
    "photorealism, no 3D render. "
)

CADRE = (
    "Full body visible from head to shoes, centered, side or three-quarter view so the "
    "exercise form is readable. Plain white background, no floor, no gym equipment "
    "unless the exercise requires it, soft contact shadow under the feet. "
)

INTERDITS = (
    "No text, no letters, no numbers, no logo, no watermark, no signature, no frame "
    "border. No extra limbs, no deformed hands, no missing feet. Not sexualized: this "
    "is an instructional fitness illustration, neutral and professional. "
)


# ====================================================== LES EXERCICES
# Chaque entrée décrit la POSE ET LA FORME (les repères techniques). Une illustration
# de programme qui montre une exécution fausse est pire qu'une absence d'illustration.

EXERCICES = {
    "squat": "performing a bodyweight squat at the bottom position, side view: thighs "
             "parallel to the ground, knees tracking over the toes, hips pushed back, "
             "chest up, back straight and neutral, arms extended forward for balance, "
             "heels flat on the ground.",
    "fente": "performing a forward lunge at the bottom position, side view: front shin "
             "vertical with the knee directly over the ankle, front thigh parallel to "
             "the ground, back knee lowered just above the floor, back heel lifted, "
             "torso upright, hands on hips.",
    "gainage": "holding a high plank, side view: body in one straight line from heels "
               "to head, hands directly under the shoulders with straight arms, core "
               "braced, hips level with the shoulders, toes on the ground, neck neutral.",
    "pompe": "at the bottom of a push-up, side view: chest just above the floor, elbows "
             "bent about forty-five degrees from the torso, body in one straight rigid "
             "line from heels to head, toes on the ground.",
    "souleve-de-terre": "performing a Romanian deadlift with a barbell, side view: hips "
                        "hinged far back, barbell tracking close to the thighs, back "
                        "flat and neutral, slight knee bend, shoulders pulled back.",
    "fessier": "performing a glute bridge at the top position, side view: shoulders on "
               "the floor, feet flat and close to the hips, hips driven high so the "
               "body forms a straight line from knees to shoulders, glutes contracted.",
    "gainage-lateral": "holding a side plank: supported on one forearm directly under "
                       "the shoulder, body in one straight line from feet to head, hips "
                       "lifted high, top arm extended vertically toward the ceiling.",
    "burpee": "at the jump phase of a burpee, dynamic full-body action pose: feet off "
              "the ground, arms extended overhead, body stretched, ponytail flying.",
    "abdos": "performing a crunch, side view: shoulder blades lifted off the floor, "
             "knees bent with feet flat, hands lightly behind the head, chin off the "
             "chest, abdominals visibly contracted.",
    "mollets": "performing a standing calf raise, side view: up on the balls of the "
               "feet at the top position, calves contracted, body tall and straight, "
               "one hand lightly touching a wall for balance.",
}


def gemini_key() -> str:
    """Même résolution que gen_seg4_narratif.py : env d'abord (secret CI), .env.local
    en repli local. Un message explicite vaut mieux qu'un traceback."""
    k = os.environ.get("GEMINI_API_KEY", "").strip()
    if k:
        return k
    env = ROOT / ".env.local"
    if env.exists():
        for line in env.read_text().splitlines():
            if line.startswith("GEMINI_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    sys.exit("[ERREUR] GEMINI_API_KEY absente (ni environnement, ni .env.local).\n"
             "        En session cloud la clé n'existe pas : lancer le workflow\n"
             "        .github/workflows/dessin-illustrations.yml, qui tourne là où le\n"
             "        secret GEMINI_API est déjà branché.")


def prompt_for(nom: str) -> str:
    return (STYLE + PERSONNAGE + "She is " + EXERCICES[nom] + " " + CADRE + INTERDITS)


def generate(nom: str, out: pathlib.Path, ratio: str, variante: int = 1) -> bool:
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        sys.exit("[ERREUR] google-genai manquant : pip install 'google-genai>=0.3'\n"
                 "        (le workflow dessin-illustrations.yml l'installe tout seul)")
    client = genai.Client(api_key=gemini_key())
    cfg = types.GenerateContentConfig(response_modalities=["IMAGE"],
                                      image_config=types.ImageConfig(aspect_ratio=ratio))
    suffix = "" if variante == 1 else f"-{variante}"
    img = out / f"{nom}{suffix}.png"
    prompt = prompt_for(nom)
    if variante > 1:
        # Varier l'angle SANS toucher au personnage : la feuille reste intacte.
        prompt += f" Alternate camera angle, variation {variante}. "
    for attempt in range(4):
        resp = client.models.generate_content(model=MODEL_IMG, contents=[prompt], config=cfg)
        for cand in (resp.candidates or []):
            for part in (getattr(getattr(cand, "content", None), "parts", None) or []):
                data = getattr(part, "inline_data", None)
                if data and data.data:
                    img.write_bytes(data.data)
                    print(f"[OK] {nom}{suffix} -> {img}", flush=True)
                    return True
        print(f"    [vide {attempt+1}/4] {nom}{suffix}", flush=True)
    print(f"[ECHEC] {nom}{suffix} — aucune image après 4 tentatives", flush=True)
    return False


def main() -> None:
    ap = argparse.ArgumentParser(description="Génère la série d'illustrations d'exercices.")
    ap.add_argument("-e", "--exercices", nargs="+", help="exercices à générer")
    ap.add_argument("--tout", action="store_true", help="toute la série")
    ap.add_argument("--variantes", type=int, default=1, help="rendus par exercice (défaut 1)")
    ap.add_argument("--ratio", default="3:4", help="ratio d'image (défaut 3:4)")
    ap.add_argument("--out", type=pathlib.Path, default=ROOT / "dessin" / "illustrations")
    ap.add_argument("--liste", action="store_true", help="liste les exercices connus")
    ap.add_argument("--prompt", metavar="EXERCICE", help="affiche le prompt sans appeler l'API")
    a = ap.parse_args()

    if a.liste:
        for k, v in EXERCICES.items():
            print(f"{k:20s} {v[:70]}…")
        return
    if a.prompt:
        print(prompt_for(a.prompt)); return

    noms = list(EXERCICES) if a.tout else (a.exercices or [])
    if not noms:
        sys.exit("Rien à générer : passer -e <exercices> ou --tout (voir --liste).")
    if inconnus := [n for n in noms if n not in EXERCICES]:
        sys.exit(f"Exercice inconnu : {', '.join(inconnus)} (voir --liste)")

    gemini_key()          # échoue TÔT et clairement, avant toute dépendance
    a.out.mkdir(parents=True, exist_ok=True)
    ko = 0
    for n in noms:
        for v in range(1, max(1, a.variantes) + 1):
            if not generate(n, a.out, a.ratio, v):
                ko += 1
    print(f"\n{len(noms)*max(1,a.variantes) - ko} image(s) écrite(s) dans {a.out}")
    sys.exit(1 if ko else 0)


if __name__ == "__main__":
    main()
