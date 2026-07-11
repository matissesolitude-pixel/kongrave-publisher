# KONGRAVE — STYLE_REFERENCE.md
### Valeurs EXTRAITES image par image du master `output/v3/EPISODE_01_kongrave.mp4`

Méthode : `ffmpeg select gt(scene,0.3)` + scans denses 0.1 s + mesure bbox pixels + relecture
`ep01_fix.sh`. Le builder `build_episode.py` doit produire un résultat **IDENTIQUE** au master.

---

## 0. RÈGLE ÉDITORIALE (bulle-choc ≠ sous-titre)
**La bulle-choc est un COMMENTAIRE ÉDITORIAL, JAMAIS un sous-titre.** Elle affiche un mot **DIFFÉRENT**
de ce qui est dit vocalement — elle souligne, ajoute une couche de sens (comic : voix « j'étais mauvais
à l'école » → bulle « CANCRE »).
- JSON : `mot_choc` = mot **AFFICHÉ** (éditorial) ; `mot_choc_anchor` = mot de la **VOIX** où caler le
  timing (jamais affiché). Le builder time sur l'ancre, affiche le mot_choc. **`mot_choc != mot_choc_anchor`**.
- ep02 : lost→**K.O.** · revenge/loves it→**TRAP** · get paid→**DISCIPLINE** · died on a revenge trade→**GRAVEYARD** · strike back→**NEXT ROUND**
- ep03 : broke→**REKT** · could be wrong→**HUMBLE** · countdown→**TICK TOCK** · blow up→**9/10** · the hard way→**LAST CHANCE**
- **Les captions jaunes RESTENT VISIBLES en permanence** (elles sous-titrent la voix). La bulle
  éditoriale se superpose PAR-DESSUS (mot différent, en haut de cadre). Les deux **coexistent** car
  ils disent des choses différentes. PLUS DE MASQUAGE de la caption pendant la bulle.

## 0bis. CTA seg5 — JAMAIS « follow me »
Le segment 5 ne finit PLUS par « follow me » (le Patriarche n'implore pas d'abonnés). Le CTA est **la RÈGLE
elle-même** : ordre / avertissement / punchline qui ferme l'épisode. Le follow est implicite. Tous les seg5
d'ep02-28 ont été réécrits en ce sens dans le JSON. Caption Instagram (séparée de la voix) = règle en une
phrase + « Comment GAME — tell me what wiped YOU out. The best stories become episodes. » + 5-6 hashtags.

## 0ter. PLANCHE BD = SAFE ZONE (doctrine, v12)
Le contenu est encadré dans une **CASE de bande dessinée** (Sin City) qui matérialise la safe zone, et
cette case est **une cellule d'une PAGE plus grande** (cases voisines visibles).
- **Case active** = rectangle à **trait noir épais** (`PANEL_BORDER=14`) ; contenu composité DEDANS.
  Bords : `ACT_TOP=250`, `ACT_BOT=1570`, `PANEL_X0=SIDE=80`, `PANEL_X1=W-SIDE=1000` (largeur 920).
- **Gouttières blanc cassé** (`GUTTER=0xEFEAE0`) **symétriques** : latérales `SIDE=80` (gauche=droite),
  verticales `VG=44` (haut=bas).
- **Cases VOISINES** (logique de planche) : bandes d'**encre noire massive** au-dessus (`y[0, ACT_TOP-VG]`)
  et en dessous (`y[ACT_BOT+VG, H]`), alignées sur la colonne, coupées par le cadre. PAS de contenu neuf,
  pas de texte dedans.
- **Le contenu remplit la case** : buste `BUSTE_W=820`, tête proche du bord haut (`BUSTE_TOP=ACT_TOP+22`),
  peut aller jusqu'au trait. Bulles au coin intérieur (peuvent mordre le trait, jamais sortir en gouttière).
- **Captions jaunes** réduites (police 46, largeur `CAP_MAXW` = intérieur de case, 2 lignes max), en bas de case.
- **Générique Veo** = **plein cadre, SANS case** ; la planche apparaît au 1er segment narratif.
- **Un seul gabarit** : constantes + `_panel_filters` dans `build_episode.py`, héritées par `autoprod.py` (ep12+).

## A. INVENTAIRE EXHAUSTIF DES BULLES DU MASTER

| # | Texte | Segment | Type | Forme / queue | Apparition → Disparition | Position (bbox px, frame 1080×1920) | Ancrage | Police |
|---|---|---|---|---|---|---|---|---|
| 1 | **WIPED OUT** | générique | — | starburst | **0.0 → ~4.0** (baké dans l'intro Veo, PAS un overlay du corps) | plein cadre (titre Veo) | — | Bangers blanc+contour |
| 2 | **REAL CAPITAL** | seg2 (buste) | dialogue | ovale, **queue ↓ droite** (tip 0.82) | **14.63 → 15.90** (1.27 s) | intérieur **(0,0)–(912,404)** ; overlay **(−70,−20)** scale **1000** | **FLUSH coin HAUT-GAUCHE** (bleed hors cadre) | Bangers **noir** ~150 |
| 3 | **DISCIPLINE** | seg3 (plein-pied) | dialogue | ovale, **queue ↓** (tip 0.66) vers la tête | **19.20 → 20.85** (1.65 s) | intérieur **(108,76)–(780,492)** | haut-gauche, petite marge | Bangers **noir** ~165 |
| 4 | **ZERO** | seg4 (plein-pied) | impact | **starburst** + trame Ben-Day | **23.50 → 24.55** (1.05 s) | cœur (420,696)–(700,912), **centre ≈ (540, 804) = y 0.42·H** | **centré H**, tiers médian | Bangers **blanc+contour** ~300 |
| 5 | **FEED THE MARKET** | seg5 (buste) | impact | **starburst** 2 lignes | **32.10 → 33.36 (fin)** (1.26 s) | **sur le VISAGE**, centre ≈ (540, ~1100) = **y 0.57·H** | **centré H, plus bas (sur le visage)** | Bangers **blanc+contour** ~170 |

**Constat clé** : dans le CORPS il n'y a que **2 impacts** (ZERO plein-pied, FEED buste) et **2 dialogues**
(REAL CAPITAL buste, DISCIPLINE plein-pied). WIPED OUT est dans le générique. seg1 du corps n'a
**qu'une caption**, pas de burst. → position d'impact **dépend du plan** : plein-pied/champ ≈ **y 0.42·H**,
buste ≈ **y 0.57·H** (sur le visage).

## B. STYLES (générateurs canoniques `bubble_gen.py`)
- **Impact** (`make_bubble`) : étoile blanche 12 pointes, contour noir 12 px, trame Ben-Day (r7 pas30),
  texte **Bangers BLANC + contour noir** (stroke 11 %), rotation −6°, 1–2 lignes. Hauteur star ≈ **560–620 px**.
  **AUCUN négatif / inversion N&B — le nœud n'existe pas dans le builder.**
- **Dialogue** = **templates Simon EXTRAITS** remplis (`bubble_fill`), Bangers **NOIR**. PAS `make_dialog`.
  - buste : **`tmpl_rc`** (queue LISSE) → scale **1000**, overlay **(−70,−20)** = flush coin HG (= master RC).
  - plein-pied : **`tmpl_disc`** (queue **ÉCLAIR** zigzag) → scale **700**, overlay **(96,64)** (= master DISCIPLINE).

## C. CAPTIONS (mesuré : boîte jaune)
- Boîte **jaune #F7E017**, contour noir, texte **Bangers NOIR** MAJ.
- Position mesurée : bbox **y 1356 → 1519** (bas ≈ **1519**), x centré (largeur ≤ ~940). Hauteur ~163.
- → overlay bas de cadre : **y = 1540 − hauteur** (bas ≈ 1519–1540). Masquées pendant un mot-choc.

## D. TIMING (la voix pilote — silencedetect −33 dB : d 0.14)
- **Mot-choc placé SUR le mot prononcé** (impact ET dialogue) : t0 = position du mot dans sa phrase − 0.10.
  Un mot en **fin de phrase** (YOU LOST, ZERO, FEED du master) tombe alors PILE **dans le silence qui suit** ;
  un mot au milieu (BLOWN, STRIKE BACK) claque **sur le mot**. Robuste dans tous les cas.
- Maintien : **impact 1.2 s** (ZERO 1.05/FEED 1.26), **dialogue 1.6 s** (DISC 1.65/RC 1.27).
- **GÉNÉRIQUE 1.2 s** : le générique VISUEL est trimé à **`GENERIQUE_DUR=1.2`** s, fenêtre climax
  `[GEN_CLIMAX=0.0, 1.2]` du clip Veo (logo KONGRAVE + éclair à ~0.5 s). Même point de coupe toute la série.
- **POSITION = FIN (PO 2026-07-11, `GENERIQUE_POSITION="end"`, gabarit ACTIF).** Cold open : l'épisode
  ouvre DIRECT sur seg1 (orage + hook), aucun générique en tête. Le générique 1.2 s passe en DERNIÈRE
  position, **après le seg5 COMPLET + `GEN_END_SILENCE=0.30` s de silence**. Charnière de boucle
  (seg5 → battement → générique → re-hook au replay). **Le générique ne mord JAMAIS les derniers mots**
  (il est entièrement APRÈS le corps). Motif PO : rétention insuffisante avec générique en tête.
  - **Audio** = corps (autonome) | 0.30 s de silence | audio Veo 1.2 s (écho + fade out 0.4 s pour une
    boucle nette). Aucun chevauchement → simple concaténation, pas de mix.
  - **Vidéo** = corps | hold 0.30 s (dernière image de seg5 figée) | générique 1.2 s.
  - **Aucun offset recalé** : captions/bulles/mots-chocs sont en TEMPS-CORPS, le générique n'entre pas
    dans leur calcul. La bascule ne touche que `gen_audio_fix` (`_gen_end`). autoprod (ep14+) hérite.
  - Vérifié sur ep07 (banc d'essai, master publié restauré ensuite) : cold open OK, seg5 complet, silence
    mesuré à −43 dB entre voix (−32) et générique (−30).
- **ARCHIVE — gabarit TÊTE (`GENERIQUE_POSITION="head"`, legacy).** Générique 1.2 s EN TÊTE, transition
  L-CUT : l'image coupe à 1.2 s mais l'audio Veo continue (`GEN_AUDIO_TAIL=1.6` s, fade + écho « bave »)
  par-dessus le 1er segment ; lit d'orage intro de 1.2 s sous le générique. **Épisodes publiés ainsi
  (INTOUCHABLES) : ep01-05, 07, 09, 10.** Code conservé dans `_gen_head`, désactivé par le drapeau.
- Clamp de chaque choc/caption à la fenêtre vidéo de son segment. LEAD 1.5 s, GAP 0.45 s.

## E. AVATAR / DÉCOR (rappel)
- Plein-pied **dos/profil UNIQUEMENT** (`output/perso_detoure/v2/{dos,profil}_clean.mov`), scale 504,
  overlay (384,834).
- **BUSTE (visage) — RÈGLE GRAVÉE : chaque épisode a ses PROPRES bustes lip-sync**, générés via
  **DomoAI Talking-Avatar** avec l'**audio ElevenLabs de CET épisode** (`regen_bustes.py <ep>` →
  `output/batch/ep{NN}/buste{2,5}_alpha.mov`, détour rembg). **On ne réutilise JAMAIS le buste d'un
  autre épisode** (sinon la bouche bouge sur le mauvais texte). Image source = `assets/buste_binaire_parfait.png`
  (face cam N&B sur blanc). Placement : scale 1080, overlay centré X, y 120. seg2 (reveal) + seg5 (cta).
  Le builder REFUSE de construire si `buste{2,5}_alpha.mov` de l'épisode est absent.
- Décor binarisé + fauteuil rouge. Orage : flashs + éclair. seg4 : voir la hiérarchie §E-bis.

## E-bis. SEG4 — HIÉRARCHIE HYPERFRAMES-FIRST (doctrine v2, PO 2026-07-11)

**Ordre de routage seg4, du défaut à l'exception. Le `seg4_type` reste EXPLICITE dans le JSON
(le code ne l'infère jamais, cf. `seg4_routing.py`), mais la doctrine d'écriture vise le prop d'abord.**

1. **DÉFAUT = `prop` (HyperFrames).** Tout seg4 commence par la question : *« quelle métaphore
   PHYSIQUE porte cette preuve ? »* — et on se creuse la tête AVANT de conclure qu'il n'y en a pas.
   Deux registres, même pipeline (`npx hyperframes render`, HTML→MP4, 8-12 s, la voix parle par-dessus,
   AUCUN texte/chiffre dans l'anim — les mots-chocs sont des overlays compositing) :
   - **2D flat motion** (canon actuel : Sisyphe ep05, dominos, briques ep30).
   - **3D Three.js/WebGL** — VALIDÉ (test échiquier, Chromium headless rend le WebGL). Objet symbolique,
     caméra lente, toon shading Sin City N&B + **un seul rouge**. Charger Three.js par `<script>` CDN
     comme GSAP ; timeline déterministe (pas de `requestAnimationFrame`, rendu dans l'`onUpdate` GSAP).
     *À affiner avant batch : encrage Sin City (le toon plat manque d'encre) + cadrage safe zone.*
   - **Économie** : un épisode prop ne coûte que **2 tâches DomoAI** (les bustes seulement, prop gratuit).
   - La bibliothèque `props/ep{NN}.html` grossit — chaque prop versionné, style unifié, **jamais réutilisé**.

2. **EXCEPTION = `narratif` (Gemini + DomoAI).** UNIQUEMENT quand la preuve exige une **SCÈNE HABITÉE**
   (lieu, atmosphère, présence humaine suggérée) qu'aucun objet-métaphore ne peut porter. La charge de la
   preuve est INVERSÉE : c'est le narratif qui doit se justifier. Coûte 3 tâches DomoAI (2 bustes + 1 i2v).
   Image Gemini **sans texte NI chiffre** (garde-fou OCR `scene_textcheck` : rejette texte imprimé ET
   chiffres/devises ; aveugle au manuscrit → prompt « scrawl illisible » + vérif visuelle pour les journaux).

3. **`champ` (champ de bataille).** Inchangé : **destruction de masse explicite uniquement**
   (s1 ep02/03/13, ou `seg4_type:"champ"` en s2). Aucun insert requis (généré depuis `champ_bataille.png`).

**Schéma v4 (saison 2, ep29+)** : chaque épisode porte `ltti_target`, `taxonomy`, `hook_cell`
(métadonnées, tolérées+loggées) et `seg4_type` sur le segment 4 (routage, **fail-loud si absent/invalide**).

## F. INTERDITS
1. JAMAIS d'inversion N&B. 2. Bangers UNIQUEMENT. 3. Plein-pied jamais de face. 4. Impacts = `make_bubble`
(jamais `make_shock`/Arial). 5. Dialogue buste = flush coin HG (−70,−20). 6. Voix pilote le timing.
