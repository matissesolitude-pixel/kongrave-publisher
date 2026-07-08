#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Inserts seg4 NARRATIFS (scènes d'ambiance) : illustration DESSINÉE (Gemini) puis ANIMÉE
(DomoAI i2v). Sin City N&B + UN rouge. Sortie : output/batch/ep{NN}/seg4_hf.mp4 (le builder
route seg4 -> ce fichier ; il ne le binarise pas, le rouge est préservé).

Usage : python gen_seg4_narratif.py <ep> --go     (payant : ~$0.10 image + ~$0.30 i2v 5s)
        python gen_seg4_narratif.py <ep>           (dry-run)
        python gen_seg4_narratif.py <ep> --anim-only   (réutilise l'image, refait l'anim)
        python gen_seg4_narratif.py <ep> --finish-only  (refait juste le contraste)

Réservé aux épisodes NARRATIFS (couloir, bureaux vides, cimetière…). Les épisodes CONCEPT
(ep05,07,09,10,15,17,19,22,24,25) utilisent des PROPS HyperFrames, pas ce script.
"""
import argparse, base64, os, subprocess, sys
from pathlib import Path
from anim_test import create_i2v, download
from avatar_to_video import load_api_key, poll_task

ROOT = Path(__file__).resolve().parent
MODEL_IMG = "gemini-3.1-flash-image"
FF = os.environ.get("FFMPEG") or "/opt/homebrew/bin/ffmpeg"
SECS = 5

STYLE = (
    "Strict binary black and white ink comic, Frank Miller Sin City style, raw heavy inking, "
    "deep blacks, very high contrast, no grayscale, no color EXCEPT one dark red element. "
    "Night, film-noir. Vertical 9:16, empty space in the upper third for a text overlay. "
    "No text, no letters, no logos, NO people anywhere. "
)

# ep -> (scene_prompt, anim_prompt)
SCENES = {
    4: ("An empty, plush five-star hotel corridor at night in strong one-point perspective, "
        "receding to a single vanishing point, ceiling lights down the center, numbered doors, "
        "a single dark red carpet runner (the ONLY red), rain at the far window, ominous.",
        "Slow forward dolly gliding down the empty corridor toward the far end, subtle light "
        "flicker, the far end sinking into darkness, keep the red carpet. No people, no text."),
    8: ("A narrow rain-soaked back alley at night, wet asphalt reflecting light, fire escapes and "
        "grimy brick walls, a single buzzing neon sign on the wall shaped as a plain glowing dark red "
        "RECTANGLE OUTLINE / abstract geometric glyph (the ONLY red) — absolutely NO words, NO letters, "
        "NO readable text of any kind on it, steam rising from a grate, violent and claustrophobic, "
        "deep noir shadows, one-point perspective.",
        "Slow tense push down the wet neon alley, the abstract red neon glow flickering (it stays a "
        "blank shape, NO text ever appears), steam drifting, faint rain, menacing stillness before "
        "violence. Frank Miller Sin City black and white ink, keep the red neon glow. No people, NO text, NO letters."),
    11: ("An open leather trading journal / ledger lying on a dark wooden desk under a single desk "
         "lamp at night, close top-down three-quarter view, pages densely covered in handwritten "
         "notes and numbers, several entries circled, one entry circled in dark red ink (the ONLY "
         "red element), a fountain pen resting on the page, intimate confessional noir mood.",
         "Slow push-in onto the open journal under the lamp, pages faintly settling, the one red "
         "circled entry drawing the eye, quiet confessional stillness. Frank Miller Sin City black "
         "and white ink, keep the one red circle. No people, no text."),
    6: ("A deserted corporate trading floor at night, long rows of empty desks with dark "
        "switched-off monitors and vacant office chairs, one chair toppled over on the floor in "
        "the foreground, a single desk lamp still glowing at the far end, cold and lifeless, one "
        "dark red office chair among the black ones (the ONLY red element), deep noir shadows.",
        "Slow cinematic dolly drifting down the aisle between the empty desks toward the single "
        "lit lamp at the far end, faint dust in the light, the toppled chair, cold ominous "
        "stillness. Frank Miller Sin City black and white ink, keep the one red chair. No people, no text."),
    12: ("A large wall mirror in a dark noir room, its glass violently cracked into a spiderweb of "
         "shards, each shard reflecting a fragment of a dim empty room, one single shard glowing dark "
         "red (the ONLY red), deep shadows, unsettling self-deception.",
         "Slow push toward the shattered mirror, faint glints traveling across the cracked shards, the "
         "red shard catching light, cold unsettling stillness. Frank Miller Sin City ink, keep the one "
         "red shard. No people, no text."),
    14: ("An empty padded asylum cell at night, one-point perspective, quilted padded walls scored "
         "with chaotic scratch marks, a heavy riveted steel door, a single caged emergency light on "
         "the ceiling glowing dark red (the ONLY red), claustrophobic and menacing.",
         "Slow unsettling push into the padded cell, the red caged light flickering, faint dust, "
         "oppressive stillness of madness. Frank Miller Sin City ink, keep the red light. No people, no text."),
    16: ("An abandoned strategy plan spread across a desk and pinned on a wall under a dim lamp at "
         "night — abstract diagrams, arrows and boxes only (NO words), edges curling, a layer of dust, "
         "one bold dark red X marked across it (the ONLY red), ignored and neglected, noir shadows.",
         "Slow drift across the dusty abandoned plan under the lamp, faint dust settling, the red X "
         "drawing the eye, quiet neglect. Frank Miller Sin City ink, keep the red X. No people, NO words, no text."),
    18: ("A shadowy industrial oil yard at night, rows of stacked steel oil barrels and dark "
         "pipework, an oil derrick silhouette against the sky, black oil pooled and glistening on the "
         "ground, one single dark red barrel among the black ones (the ONLY red), heavy noir atmosphere.",
         "Slow menacing dolly through the oil yard, faint vapor rising, black oil glistening, the red "
         "barrel standing out, ominous industrial stillness. Frank Miller Sin City ink, keep the red "
         "barrel. No people, no text."),
    20: ("Two theatrical masks hanging side by side on a dark wall under a hard spotlight — one calm "
         "and composed, one twisted and arrogant — deep noir shadows, one mask tinted dark red (the "
         "ONLY red), theatrical and psychological.",
         "Slow push between the two masks, the spotlight subtly shifting, the red mask catching light, "
         "tense psychological stillness. Frank Miller Sin City ink, keep the one red mask. No people, no text."),
    21: ("A deserted high-stakes casino table at night — dark felt, scattered playing cards and "
         "stacks of chips, a roulette wheel in shadow behind — lit by a single low hanging lamp, one "
         "single dark red casino chip in the foreground (the ONLY red), the house's empty domain.",
         "Slow dolly across the abandoned casino table under the lamp, a card faintly settling, the "
         "red chip catching light, cold predatory stillness. Frank Miller Sin City ink, keep the red "
         "chip. No people, no text."),
    23: ("A calm, orderly empty trading desk at night, all monitors switched off and dark, everything "
         "neat and still, a single small desk lamp casting a warm pool of light, one dark red object "
         "on the desk (the ONLY red), serene disciplined silence.",
         "Very slow gentle push toward the tidy dark desk and the single lamp, dust motes drifting "
         "calmly in the light, deep peaceful stillness. Frank Miller Sin City ink, keep the one red "
         "object. No people, no text."),
    26: ("A foggy graveyard at night in perspective, rows of weathered BLANK tombstones (no "
         "inscriptions, no words) receding into mist, bare trees, a wrought-iron gate, one single "
         "dark red rose lying on the ground (the ONLY red), mournful noir atmosphere.",
         "Slow solemn dolly through the rows of blank tombstones into the fog, mist drifting, the red "
         "rose catching faint light, funereal stillness. Frank Miller Sin City ink, keep the red rose, "
         "tombstones stay BLANK. No people, NO text, NO letters."),
    27: ("A dark deserted office at night with switched-off screens, and in the foreground a single "
         "heavy door standing ajar with warm daylight spilling through the gap, the door painted dark "
         "red (the ONLY red), an invitation to walk away, calm noir.",
         "Slow push toward the red door ajar with light spilling through, faint dust in the light "
         "beam, the dark office behind, calm decisive stillness. Frank Miller Sin City ink, keep the "
         "red door. No people, no text."),
    28: ("A tall grand ornate mirror standing in a dark empty room, its baroque frame catching a "
         "sliver of light, the glass reflecting the dim shadowy room back, the frame tinted dark red "
         "(the ONLY red), intimate and confrontational, deep noir.",
         "Slow push straight toward the grand mirror, the reflection deepening, faint light traveling "
         "across the red frame, confrontational stillness. Frank Miller Sin City ink, keep the red "
         "frame. No people, no text."),
}


def gemini_key():
    # CI-first : os.environ (secret GitHub) d'abord, .env.local en fallback local.
    k = os.environ.get("GEMINI_API_KEY", "").strip()
    if k:
        return k
    env = ROOT / ".env.local"
    if env.exists():
        for line in env.read_text().splitlines():
            if line.startswith("GEMINI_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    sys.exit("[ERREUR] GEMINI_API_KEY absente (ni env CI ni .env.local). Vérifie le secret GitHub.")


def gen_image(scene, img):
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=gemini_key())
    cfg = types.GenerateContentConfig(response_modalities=["IMAGE"],
                                      image_config=types.ImageConfig(aspect_ratio="9:16"))
    for attempt in range(3):
        resp = client.models.generate_content(model=MODEL_IMG, contents=[STYLE + scene], config=cfg)
        for cand in (resp.candidates or []):
            for part in (getattr(getattr(cand, "content", None), "parts", None) or []):
                data = getattr(part, "inline_data", None)
                if data and data.data:
                    img.write_bytes(data.data); print(f"[OK] image -> {img}"); return
        print(f"    [vide {attempt+1}/3]")
    sys.exit("[ECHEC] Gemini : pas d'image.")


def animate(anim, img, raw):
    api_key = load_api_key()
    b64 = base64.b64encode(img.read_bytes()).decode("ascii")
    print(f"[i2v] DomoAI {SECS}s …")
    tid = create_i2v(api_key, b64, SECS, anim)
    url = poll_task(api_key, tid)
    download(url, raw)
    print(f"[OK] i2v brut -> {raw} ({raw.stat().st_size/1024/1024:.1f} Mo)")


def finish(raw, dst):
    vf = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,eq=contrast=1.35:saturation=1.25,fps=30"
    subprocess.run([FF, "-y", "-v", "error", "-i", str(raw), "-an", "-vf", vf,
                    "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", str(dst)], check=True)
    print(f"[OK] insert seg4 -> {dst}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ep", type=int)
    ap.add_argument("--go", action="store_true")
    ap.add_argument("--anim-only", action="store_true")
    ap.add_argument("--finish-only", action="store_true")
    a = ap.parse_args()
    if a.ep not in SCENES:
        sys.exit(f"[ERREUR] pas de scène narrative définie pour ep{a.ep:02d} (dict SCENES).")
    scene, anim = SCENES[a.ep]
    d = ROOT / "output" / "batch" / f"ep{a.ep:02d}"; d.mkdir(parents=True, exist_ok=True)
    img = ROOT / "assets" / f"scene_seg4_ep{a.ep:02d}.png"
    raw = d / "seg4_i2v_raw.mp4"; dst = d / "seg4_hf.mp4"
    if a.finish_only:
        finish(raw, dst); return
    if not a.go:
        print(f"[DRY-RUN ep{a.ep:02d}] --go pour générer (~$0.10 image + ~$0.30 i2v).")
        print("SCENE:", scene[:90], "…"); return
    if not a.anim_only:
        gen_image(scene, img)
    animate(anim, img, raw)
    finish(raw, dst)


if __name__ == "__main__":
    main()
