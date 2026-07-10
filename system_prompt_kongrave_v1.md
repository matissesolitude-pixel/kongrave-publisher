# SYSTEM PROMPT — KONGRAVE (Le Patriarche Noir) v1

Règles PERMANENTES de production des Reels KONGRAVE. Paramètres exacts (positions, tailles, timing) :
voir `STYLE_REFERENCE.md`. Le builder est `build_episode.py` (JSON `KONGRAVE_episodes_02_to_28_v3.json`).
Référence absolue de style = master validé `output/v3/EPISODE_01_kongrave.mp4`.

## 0. Hook & copywriting → `LTTI_PROFILES.md` (source canonique)

**RÈGLE DE BASE : tout script KONGRAVE s'écrit POUR un profil.** La matrice de hook (doctrine v1.1),
les 16 profils LTTI (canon V2, avec leurs « registres forts » = cellules qui marchent par profil), les
4 familles, les garde-fous compliance et le schéma de tags JSON (`ltti_target` + `hook_cell`) vivent
dans **`LTTI_PROFILES.md`** (racine) — qui **fait autorité sur le copywriting**. Ne pas dupliquer ici.

Rappels non négociables (le détail est dans le fichier) :
- **Un hook = UNE cellule** (profil × variable × regard × temps + valence). Jamais deux variables ni
  deux regards. **Fraîcheur :** jamais deux épisodes consécutifs sur la même cellule.
- **Axes orthogonaux :** le temps est neutre ; c'est **regard × valence** qui colore la période.
- **Le dream outcome est une IDENTITÉ, jamais un chiffre.** Aucun montant, aucune promesse de gain
  (garde-fou compliance). Le nightmare est le terrain naturel de KONGRAVE.
- ep29+ : chaque épisode porte ses tags `ltti_target` / `hook_cell` (cf. `LTTI_PROFILES.md` §5).

## 1. Bulles éditoriales (RÈGLE CENTRALE)
- La bulle-choc **ne répète JAMAIS** ce qui est dit vocalement. C'est un **commentaire éditorial** :
  elle souligne le propos avec un mot **DIFFÉRENT**. La voix porte le message, la bulle ajoute une
  couche de sens (comic : voix « j'étais mauvais à l'école » → bulle « CANCRE »).
  - **Interdit** : voix « You just lost » → bulle « YOU LOST » (répétition).
- JSON : `mot_choc` = mot **AFFICHÉ** (éditorial, jamais un mot de la phrase) ; `mot_choc_anchor` =
  mot de la **VOIX** où caler le timing (jamais affiché).
- Les **captions jaunes restent visibles en permanence** (sous-titre de la voix). La bulle se superpose
  par-dessus, en haut de cadre. Les deux **coexistent** (mots différents). Aucun masquage.

## 2. Avatar (doctrine dos/profil)
- Plans **plein-pied = TOUJOURS dos ou profil**, JAMAIS de visage de face (le visage dérive en i2v).
- Le **visage n'apparaît QUE sur les bustes lip-sync** (seg2 reveal, seg5 cta).
- **Bustes lip-sync PROPRES à chaque épisode** : générés via DomoAI Talking-Avatar avec l'audio
  ElevenLabs de CET épisode (`regen_bustes.py <ep>`). **JAMAIS réutiliser le buste d'un autre épisode**
  (sinon la bouche bouge sur le mauvais texte). Le builder refuse de construire sans eux.
- Plein-pied dos/profil = clips DomoAI régénérés sur fond blanc puis détourés (`regen_dosprofil.py`).

## 3. Mots-chocs — 2 styles (générateurs canoniques `bubble_gen.py`)
- **Impact** = starburst blanc, contour noir, trame Ben-Day, Bangers BLANC+contour (`make_bubble`).
  Position : plein-pied 0.28·H (au-dessus du perso), champ 0.42·H, buste 0.57·H (sur le visage).
- **Dialogue** = template Simon extrait (`bubble_fill` : `tmpl_rc` buste queue lisse / `tmpl_disc`
  plein-pied queue éclair), Bangers NOIR, flush coin haut-gauche.
- **INTERDIT ABSOLU : aucune inversion / négatif N&B.** Jamais de police par défaut (Bangers only).
  Jamais de burst générique `make_shock`.

## 4. Timing & structure
- **Générique 1.2 s EN FIN (cold open, PO 2026-07-11)** : l'épisode ouvre DIRECT sur seg1 (orage + hook) ;
  le générique passe après seg5 complet + 0.30 s de silence (charnière de boucle). Détail : `STYLE_REFERENCE.md`.
  Gabarit tête (générique 4 s / 1.2 s en tête) = legacy archivé (ep01-05, 07, 09, 10 publiés ainsi).
- LEAD 1.5 s d'orage avant seg1, GAP 0.45 s entre segments.
- Voix ElevenLabs pilote tout (silencedetect). Mot-choc placé sur son **ancre** (position du mot).
- Décor binarisé + fauteuil rouge. Captions jaunes #F7E017, Bangers noir, bas de cadre.
- seg4 = champ de bataille UNIQUEMENT si destruction de masse (ep02/03/13) ; sinon insert concept
  (HyperFrames).

## 4bis. CTA seg5 — PAS de « follow me »
- Le segment 5 ne finit **JAMAIS** par « follow me ». Le Patriarche ne quémande pas d'abonnés.
- Le CTA = **la RÈGLE elle-même** : un ordre, un avertissement, une punchline qui **ferme** l'épisode.
- Le follow est **implicite** : si le contenu frappe, les gens suivent sans qu'on le demande.
- (Caption Instagram, à part de la voix) : règle en une phrase + « Comment GAME — tell me what wiped YOU out.
  The best stories become episodes. » + 5-6 hashtags.

## 5. Process & garde-fous
- Un épisode à la fois, STOP validation avant export. Ne jamais reconstruire un master validé.
- Générations payantes (DomoAI ~$0.6/épisode bustes) : autorisées dans ce pipeline, mais tracées.
