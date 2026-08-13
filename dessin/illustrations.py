#!/usr/bin/env python3
"""
DESSIN — illustrations.py — LES 11 EXERCICES DU PROTOCOLE POSTÉRIEUR.

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
  python3 dessin/illustrations.py -e hip-thrust rdl bulgare
  python3 dessin/illustrations.py --seance A
  python3 dessin/illustrations.py --tout --variantes 2
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
    "Full body visible from head to shoes, centered, framed so the exercise form is "
    "unambiguous. Plain white background. Draw ONLY the equipment the exercise "
    "requires, in the same flat inked style as the figure, and never more. Soft contact "
    "shadow under the contact points. "
)

INTERDITS = (
    "No text, no letters, no numbers, no logo, no watermark, no signature, no frame "
    "border. No extra limbs, no deformed hands, no missing feet. Not sexualized: this "
    "is an instructional fitness illustration, neutral and professional. "
)


# ====================================================== LES EXERCICES
# Les 11 exercices du PROTOCOLE POSTÉRIEUR, dans l'ordre du programme.
# Chaque description reprend le REPÈRE technique du document — pas une pose « qui
# ressemble à ». Une illustration de programme qui montre une exécution fausse est pire
# qu'une absence d'illustration : elle enseigne le défaut. Les repères qui décident du
# résultat (tibias verticaux, bassin en rétroversion, pointes vers l'extérieur, hanche
# en légère extension) sont donc écrits explicitement dans le prompt.
# Format : slug -> (numéro, séance, titre FR, description EN)

EXERCICES = {
    "hip-thrust": (
        1, "A", "Hip thrust barre",
        "performing a barbell hip thrust at the top lockout, side view: upper back "
        "resting on a flat bench, a loaded barbell with a thick pad across the hips, "
        "hips fully extended so the torso and thighs form one straight horizontal line, "
        "shins strictly vertical with the feet flat, chin tucked, ribs down, pelvis "
        "posteriorly tilted with no lower-back arch, a resistance band around the knees."),
    "traineau": (
        2, "A", "Traîneau lesté",
        "pushing a weighted sled across the floor, side view: both arms extended onto "
        "the sled uprights, torso leaned forward at about forty-five degrees, one leg "
        "driving powerfully behind with the heel lifted, the other knee driving forward, "
        "a heavy plate-loaded sled, powerful marching drive and not a run."),
    "rdl": (
        3, "A", "Soulevé de terre roumain",
        "performing a Romanian deadlift at the bottom of the movement, side view: hips "
        "pushed far back in a hip hinge, barbell tracking in contact with the thighs "
        "just below the knees, back completely flat and neutral, legs semi-straight with "
        "a slight knee bend, shoulders pulled back, head in line with the spine."),
    "bulgare": (
        4, "A", "Split squat bulgare",
        "performing a Bulgarian split squat at the bottom position, side view: rear foot "
        "elevated on a flat bench behind her, front foot planted far from the bench, "
        "front thigh below parallel in deep hip flexion, torso leaning slightly forward "
        "to load the hip, rear knee lowered toward the floor, a dumbbell in each hand."),
    "abduction-penchee": (
        5, "A", "Abduction machine, buste penché",
        "using a seated hip abduction machine with the torso leaned far forward, side "
        "three-quarter view: hip flexed to about ninety degrees, chest low over the "
        "thighs, hands gripping the front of the machine, knees pushed wide apart "
        "against the pads at full spread, toes clearly turned outward."),
    "abduction-poulie": (
        6, "A", "Abduction debout à la poulie",
        "performing a standing cable hip abduction, front three-quarter view: an ankle "
        "strap on the working leg connected by cable to a low pulley, standing tall and "
        "holding the machine frame for balance, the working leg lifted out to the side "
        "and kept slightly behind the body line, toe turned outward, hip in slight "
        "extension, pelvis level."),
    "hip-thrust-unilateral": (
        7, "B", "Hip thrust unilatéral",
        "performing a single-leg hip thrust at the top position, side view: upper back "
        "on a flat bench, one foot planted with the shin vertical, the other leg lifted "
        "and held with the knee bent, hips fully extended, shoulder line perfectly "
        "horizontal, chin tucked, ribs down, no lower-back arch."),
    "extension-45": (
        8, "B", "Extension banc 45°",
        "performing a forty-five degree back extension at the top position, side view: "
        "hips on the angled pad, feet on the platform turned outward, body finishing "
        "perfectly straight and never arched beyond the body line, pelvis posteriorly "
        "tilted with the upper back deliberately rounded, arms crossed on the chest."),
    "step-up": (
        9, "B", "Step-up haut",
        "performing a high step-up, side view: stepping onto a plyo box at knee height "
        "or higher, the top leg fully driving the body upward with deep hip flexion at "
        "the start of the movement, the bottom leg hanging with no push at all, torso "
        "slightly forward, a dumbbell in each hand."),
    "abduction-droit": (
        10, "B", "Abduction machine, buste droit",
        "using a seated hip abduction machine with an upright torso, front view: back "
        "flat against the backrest, glutes staying on the seat, hands on the side "
        "handles, knees pushed wide apart against the pads at maximum spread, "
        "shoulders relaxed and down."),
    "nordic-curl": (
        11, "B", "Nordic curl",
        "performing a Nordic hamstring curl mid-descent, side view: kneeling on a pad "
        "with the ankles anchored under a fixed support, body held in one straight rigid "
        "line from knees to head with no hip bend, leaning forward under control, arms "
        "reaching down ready to catch the floor, hamstrings visibly under tension."),
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
    return (STYLE + PERSONNAGE + "She is " + EXERCICES[nom][3] + " " + CADRE + INTERDITS)


def nom_fichier(nom: str, variante: int) -> str:
    """Préfixé par le numéro du programme : les fichiers se rangent dans l'ordre des
    séances, pas dans l'ordre alphabétique."""
    num, _, _, _ = EXERCICES[nom]
    suffix = "" if variante == 1 else f"-v{variante}"
    return f"{num:02d}-{nom}{suffix}.png"


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
    img = out / nom_fichier(nom, variante)
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
                    print(f"[OK] {img.name}", flush=True)
                    return True
        print(f"    [vide {attempt+1}/4] {nom}", flush=True)
    print(f"[ECHEC] {nom} — aucune image après 4 tentatives", flush=True)
    return False


def main() -> None:
    ap = argparse.ArgumentParser(description="Génère la série d'illustrations d'exercices.")
    ap.add_argument("-e", "--exercices", nargs="+", help="exercices à générer")
    ap.add_argument("--tout", action="store_true", help="les 11 exercices du protocole")
    ap.add_argument("--seance", choices=["A", "B", "a", "b"], help="une seule séance")
    ap.add_argument("--variantes", type=int, default=1, help="rendus par exercice (défaut 1)")
    ap.add_argument("--ratio", default="3:4", help="ratio d'image (défaut 3:4)")
    ap.add_argument("--out", type=pathlib.Path, default=ROOT / "dessin" / "illustrations")
    ap.add_argument("--liste", action="store_true", help="liste les exercices connus")
    ap.add_argument("--prompt", metavar="EXERCICE", help="affiche le prompt sans appeler l'API")
    a = ap.parse_args()

    if a.liste:
        for k, (num, seance, titre, _) in EXERCICES.items():
            print(f"{num:02d}  séance {seance}  {k:24s} {titre}")
        return
    if a.prompt:
        print(prompt_for(a.prompt)); return

    if a.seance:
        noms = [k for k, v in EXERCICES.items() if v[1] == a.seance.upper()]
    else:
        noms = list(EXERCICES) if a.tout else (a.exercices or [])
    if not noms:
        sys.exit("Rien à générer : passer -e <exercices>, --seance A|B ou --tout (voir --liste).")
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
