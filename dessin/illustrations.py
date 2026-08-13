#!/usr/bin/env python3
"""
DESSIN — illustrations.py — ILLUSTRATIONS D'EXERCICES (n'importe lequel).

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

TROIS ENTRÉES
  · les 11 exercices du PROTOCOLE POSTÉRIEUR, repères écrits à la main d'après le document ;
  · --libre "n'importe quel exercice" : les repères techniques sont déduits par le modèle
    de texte AVANT de dessiner, parce qu'un nom d'exercice seul produit une pose qui
    ressemble à l'exercice, avec ses défauts de forme les plus courants ;
  · --repere "…" : les repères imposés à la main, quand on sait exactement ce qu'on veut.

DEUX STYLES
  --style encre (défaut) : noir et blanc, transcrit des illustrations de référence.
  --style couleur : même construction, aplats deux tons.
Et `dessin/references/` : toute image déposée là est envoyée comme référence VISUELLE de
style, ce qui verrouille le trait bien mieux que le prompt seul.

USAGE
  python3 dessin/illustrations.py --liste
  python3 dessin/illustrations.py -e hip-thrust rdl bulgare
  python3 dessin/illustrations.py --seance A
  python3 dessin/illustrations.py --tout --variantes 2
  python3 dessin/illustrations.py --libre "tirage horizontal poulie basse"
  python3 dessin/illustrations.py --libre "développé militaire" --style couleur
"""
from __future__ import annotations

import argparse
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODEL_IMG = "gemini-3.1-flash-image"        # même modèle que gen_seg4_narratif.py
# Modèle de TEXTE, utilisé seulement pour déduire les repères d'un exercice libre.
# Surchargeable si le nom change : GEMINI_TEXT_MODEL=... python3 dessin/illustrations.py
MODEL_TXT = os.environ.get("GEMINI_TEXT_MODEL", "gemini-3.1-flash")


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

# ====================================================== LES STYLES
# `encre` est transcrit des deux illustrations de référence, trait par trait. Les
# quatre gestes qui les caractérisent — et qu'aucun prompt vague ne produit :
#   · TOUT trait est fuselé (il enfle puis meurt en pointe), jamais d'épaisseur constante ;
#   · le muscle est CREUSÉ par des paquets de traits courts, il n'est pas cerné ;
#   · cheveux et tissu sont des MASSES NOIRES PLEINES traversées de réserves blanches ;
#   · les plis RAYONNENT depuis les points de tension du vêtement.

STYLE_ENCRE = (
    "Black ink illustration on pure white. No grey, no colour, no halftone, no gradient. "
    "Every single line is a tapered brush stroke that swells in the middle and dies in a "
    "fine point — never a constant-width outline. Muscle definition is CARVED with "
    "clusters of short tapered strokes (abdominals, obliques, serratus, deltoid, biceps, "
    "quadriceps, calves), not drawn as outlines. Hair and clothing are SOLID BLACK "
    "MASSES with white reserve slashes cutting through them to describe strands, folds "
    "and highlights. Fabric folds are clusters of thin tapered lines radiating from the "
    "stress points. Confident vector-inked commercial illustration, very high contrast, "
    "crisp edges. Stylized athletic female anatomy: broad shoulders, defined abdominals, "
    "very narrow waist, powerful glutes and thighs. "
)

STYLE_COULEUR = (
    STYLE_ENCRE.replace(
        "Black ink illustration on pure white. No grey, no colour, no halftone, no gradient. ",
        "Inked colour illustration on pure white. Flat colour fills with exactly two "
        "tones per material and crisp cel-shaded shadow edges, one light source from the "
        "upper left. No gradient, no airbrush, no photorealism, no 3D render. ")
    .replace("Hair and clothing are SOLID BLACK MASSES",
             "Hair and clothing are SOLID SATURATED MASSES")
)

STYLES = {"encre": STYLE_ENCRE, "couleur": STYLE_COULEUR}
STYLE = STYLE_ENCRE

CADRE = (
    "Full body visible from head to shoes, centered, framed so the exercise form is "
    "unambiguous. Plain white background, no ground line, no scenery. Draw ONLY the "
    "equipment the exercise requires, inked in the same style as the figure, and never "
    "more. "
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


def repere_auto(exercice: str) -> str:
    """N'IMPORTE QUEL EXERCICE. Les 11 du protocole portent leurs repères écrits à la
    main ; pour tous les autres, on demande d'abord au modèle de TEXTE la description
    technique du mouvement, puis on la donne au modèle d'image.

    Pourquoi ce détour plutôt que de jeter le nom de l'exercice dans le prompt : sans
    repères, le modèle dessine une pose qui RESSEMBLE à l'exercice, avec les défauts de
    forme les plus courants — et une illustration de programme qui montre une exécution
    fausse enseigne le défaut. Si l'appel échoue, on continue quand même : une consigne
    générique vaut mieux qu'un plantage."""
    demande = (
        f"Describe, in one dense English sentence and nothing else, how to draw a person "
        f"performing the exercise '{exercice}' with textbook technique, at the position "
        f"of peak muscular tension. State the camera view, the joint angles, the spine "
        f"position, the foot and hand placement, and the equipment. Use the technical "
        f"cues a strength coach would correct. No preamble, no bullet points.")
    try:
        from google import genai
        client = genai.Client(api_key=gemini_key())
        r = client.models.generate_content(model=MODEL_TXT, contents=[demande])
        txt = (getattr(r, "text", "") or "").strip().replace("\n", " ")
        if len(txt) > 40:
            print(f"    [repères] {txt[:110]}…", flush=True)
            return txt
    except Exception as e:                                   # modèle indisponible, quota…
        print(f"    [repères indisponibles : {type(e).__name__}] "
              f"consigne générique", flush=True)
    return (f"performing the exercise '{exercice}' with textbook technique, at the "
            f"position of peak muscular tension, in the camera view that makes the form "
            f"unambiguous, with the equipment the exercise requires")


def prompt_for(nom: str, libre: str | None = None, repere: str | None = None) -> str:
    if libre:
        corps = repere or repere_auto(libre)
    else:
        corps = EXERCICES[nom][3]
    return (STYLE + PERSONNAGE + "She is " + corps + " " + CADRE + INTERDITS)


def references() -> list:
    """Images de style optionnelles (`dessin/references/`). Le prompt seul porte déjà le
    style ; une référence VISUELLE le verrouille beaucoup plus fermement.
    N'y mettre que des images qu'on possède ou qu'on a licenciées — le dossier est
    délibérément vide dans le dépôt."""
    d = ROOT / "dessin" / "references"
    if not d.is_dir():
        return []
    return sorted(f for f in d.iterdir()
                  if f.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp"))


def nom_fichier(nom: str, variante: int, libre: str | None = None) -> str:
    """Préfixé par le numéro du programme : les fichiers se rangent dans l'ordre des
    séances, pas dans l'ordre alphabétique. Un exercice libre part sans numéro."""
    suffix = "" if variante == 1 else f"-v{variante}"
    if libre:
        slug = "".join(c if c.isalnum() else "-" for c in libre.lower()).strip("-")
        while "--" in slug:
            slug = slug.replace("--", "-")
        return f"{slug}{suffix}.png"
    return f"{EXERCICES[nom][0]:02d}-{nom}{suffix}.png"


def generate(nom: str, out: pathlib.Path, ratio: str, variante: int = 1,
             libre: str | None = None, repere: str | None = None) -> bool:
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        sys.exit("[ERREUR] google-genai manquant : pip install 'google-genai>=0.3'\n"
                 "        (le workflow dessin-illustrations.yml l'installe tout seul)")
    client = genai.Client(api_key=gemini_key())
    cfg = types.GenerateContentConfig(response_modalities=["IMAGE"],
                                      image_config=types.ImageConfig(aspect_ratio=ratio))
    img = out / nom_fichier(nom, variante, libre)
    prompt = prompt_for(nom, libre, repere)
    if variante > 1:
        # Varier l'angle SANS toucher au personnage : la feuille reste intacte.
        prompt += f" Alternate camera angle, variation {variante}. "
    contents = [prompt]
    for ref in references():          # références de style : elles verrouillent le trait
        contents.append(types.Part.from_bytes(data=ref.read_bytes(),
                                              mime_type=f"image/{ref.suffix.lstrip('.').replace('jpg','jpeg')}"))
    if len(contents) > 1:
        contents[0] += (f" Match the drawing style of the {len(contents)-1} reference "
                        f"image(s) provided: same line quality, same rendering of muscle, "
                        f"hair and fabric. Do not copy their pose or their subject.")
    for attempt in range(4):
        resp = client.models.generate_content(model=MODEL_IMG, contents=contents, config=cfg)
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
    ap.add_argument("--libre", nargs="+", metavar="EXERCICE",
                    help="n'importe quel exercice, hors protocole (repères déduits)")
    ap.add_argument("--repere", help="repères techniques imposés (avec --libre, un seul)")
    ap.add_argument("--style", choices=list(STYLES), default="encre",
                    help="encre (noir et blanc, défaut) ou couleur")
    ap.add_argument("--liste", action="store_true", help="liste les exercices connus")
    ap.add_argument("--prompt", metavar="EXERCICE", help="affiche le prompt sans appeler l'API")
    a = ap.parse_args()
    global STYLE
    STYLE = STYLES[a.style]

    if a.liste:
        for k, (num, seance, titre, _) in EXERCICES.items():
            print(f"{num:02d}  séance {seance}  {k:24s} {titre}")
        return
    if a.prompt:
        print(prompt_for(a.prompt, None if a.prompt in EXERCICES else a.prompt,
                         a.repere)); return

    if a.libre:
        gemini_key()
        a.out.mkdir(parents=True, exist_ok=True)
        ko = 0
        for ex in a.libre:
            for v in range(1, max(1, a.variantes) + 1):
                if not generate("", a.out, a.ratio, v, libre=ex,
                                repere=a.repere if len(a.libre) == 1 else None):
                    ko += 1
        sys.exit(1 if ko else 0)

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
