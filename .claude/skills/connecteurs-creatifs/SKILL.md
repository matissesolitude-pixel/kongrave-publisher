---
name: connecteurs-creatifs
description: Les connecteurs créatifs annoncés par Anthropic dans "Claude for Creative Work" (Adobe, Blender, Ableton, Splice, Autodesk Fusion, SketchUp, Resolume, Affinity by Canva) — ce que chacun fait, lesquels servent réellement à la production KONGRAVE / LA LIGNE, et comment les activer. Charge cette skill quand on parle de brancher Claude sur un outil créatif, de Photoshop/Illustrator/Firefly, de Blender ou de 3D, de sound design, de banque de samples, de connecteurs MCP créatifs, ou quand on se demande "est-ce que Claude peut piloter tel logiciel".
---

# CONNECTEURS CRÉATIFS — ce qui existe, et ce qui sert ici

## Ce que la page annonce réellement

`anthropic.com/news/claude-for-creative-work` (28/04/2026) n'annonce **pas des skills** :
elle annonce **neuf connecteurs MCP** vers des logiciels créatifs, plus Claude Design
(Anthropic Labs) et trois partenariats écoles (RISD, Ringling, Goldsmiths). Les connecteurs
sont disponibles sur **tous les plans, Free compris**.

Un connecteur ≠ une skill. Une **skill** est un document de méthode qui vit dans ce repo
(`.claude/skills/`) et charge des règles. Un **connecteur** est un serveur MCP qui donne à
Claude des outils pour agir dans un logiciel tiers — il s'active dans le compte, pas dans
le repo.

## Les neuf

| Connecteur | Ce qu'il fait |
|---|---|
| **Adobe for creativity** | 50+ outils sur Creative Cloud — Photoshop, Illustrator, Lightroom, Premiere, InDesign, Express, Firefly, Adobe Stock. Claude choisit l'outil, l'ordre et les paramètres. |
| **Affinity by Canva** | Tâches de production répétitives : réglages d'image en lot, renommage de calques, export de fichiers. |
| **Blender** | Interface langage naturel vers l'API Python. Construit sur MCP ouvert, donc utilisable hors Claude. |
| **Autodesk Fusion** | Créer et modifier des modèles 3D par la conversation (abonnement Fusion requis). |
| **SketchUp** | Transforme une conversation en point de départ de modélisation 3D. |
| **Resolume Arena / Avenue** | Contrôle temps réel pour VJ et visuels live. |
| **Resolume Wire** | Même chose côté patching nodal. |
| **Ableton** | Ancre les réponses de Claude dans la doc officielle Live et Push (documentation, pas pilotage). |
| **Splice** | Recherche dans le catalogue de samples libres de droits depuis Claude. |

## Ce qui sert vraiment à KONGRAVE — et ce qui ne sert pas

**Aucun de ces connecteurs ne dessine LA LIGNE.** Les moteurs sont du SVG/HTML animé en
GSAP et rendu par Chromium, entièrement dans ce repo. Pour dessiner un épisode, l'outil
c'est `ligne/frames.py` et la skill `revue-visuelle` — pas un connecteur.

Là où ils ont une valeur réelle, en revanche :

- **Adobe (Photoshop / Firefly) et Affinity** — la chaîne d'assets KONGRAVE : les bustes
  (`assets/buste_*.png`, `regen_bustes.py`), le détourage (`detourage_video.py`, aujourd'hui
  en `rembg`/isnet-anime), les scènes narratives (aujourd'hui en Gemini image via
  `google-genai`). Un batch d'ajustements ou un export en lot y remplacerait du code maison.
- **Splice + Ableton** — les SFX « par touche » de LA LIGNE (`pop`, `whoosh`, `thunk`, `tick`,
  `riser`, `resolve`). Ils sont **synthétisés** par `build_ligne.py`, sans banque externe :
  c'est un choix qui tient, et Splice ne vaut le détour que si on veut sortir de la synthèse.
- **Blender / Fusion / SketchUp** — hors périmètre actuel (aucune 3D dans le pipeline).
  À regarder seulement si un format futur en demande.
- **Resolume** — sans objet ici (visuel live, pas de Reels).

## Comment on les active

Dans **Claude → Réglages → Connecteurs**, côté compte. Ce sont des connecteurs hébergés
avec authentification par compte (OAuth au premier usage) : ils ne se déclarent pas dans un
`.mcp.json` du repo, et rien à committer.

**Aucune URL de serveur MCP n'est écrite ici volontairement.** Les URL exactes n'ont pas pu
être vérifiées (l'egress de l'environnement cloud bloque `anthropic.com`), et une URL
inventée dans un fichier de config est pire qu'une absence : elle échoue silencieusement et
on cherche la panne ailleurs. Les activer depuis l'interface donne les bonnes valeurs.
