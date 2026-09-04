# ÉTAT DU CHANTIER — publication KONGRAVE

Écrit le 04/09/2026 avant extinction de la machine. Tout ce qui suit est vérifié,
pas supposé.

---

## OÙ ÇA EN EST

**Les deux chaînes tournent, et les files sont pleines pour la première fois.**

```
file reels        L105  L106
file carrousel    B6 B7 (BOFU lavande) · C19 → C25 (sept MOFU)
publiés           … L102 (03/09 15:08) · L103 (04/09 04:49) · L104 (04/09 17:42)
scripts prêts     L107 L108, moteurs écrits, non fabriqués
```

**Objectif de rythme, décidé le 02/09 :** 2 reels + 1 carrousel par jour. La grille
fait 3 de large et `MIN_SPACING = 2`, donc un carrousel tous les 3 posts tombe
exactement une fois par jour ET toujours dans la même colonne. Le rythme demandé
et la règle de colonne sont la même contrainte.

Réglages en vigueur : `ligne/config.json` → `cadence_hours = 11` ·
`publish_carrousel.py` → `CADENCE_HOURS = 18`, `MIN_SPACING = 2` · les deux
workflows de publication sondent **toutes les heures**.

---

## LA DERNIÈRE CHOSE FAITE ET VÉRIFIÉE

`L105` a été **retiré de la file, corrigé et refabriqué** — la refabrication est
terminée en succès (`run 33895053188`) et il est revenu en file.

Motif : sa morale était `The fifth confirmation never comes free.`, c'est-à-dire
exactement la formule que la doctrine du 04/09 donne en contre-exemple, et son
segment 3 décrivait un état intérieur au lieu d'un fait de marché.

`L104` a été **volontairement laissé tel quel** : vérifié, déjà conforme
(segment 3 à 68 caractères, morale = une règle applicable). Il est publié depuis.

---

## CE QUI EST EN COURS, NON FINI

**Rien ne tourne.** Aucune fabrication, aucune publication en vol.

**Modifications non enregistrées dans le dépôt PARENT** (`~/disruptive-reels-pipeline`,
dépôt local sans remote) — elles ne sont pas de moi, elles viennent d'une autre
session :

```
M  DOCTRINE_LIQUIDITE_EDUCATION.md
M  alpha_assemble.py
M  avatar_to_video.py
M  ligne/GABARIT_EPISODE.md
M  carrousel/prepare_publish.py
M  carrousel/ship.sh
```

**Ne pas les committer à l'aveugle.** Demander à qui elles appartiennent avant.

---

## LA PROCHAINE ACTION, PRÉCISE

1. **Vérifier que la publication a repris** après le redémarrage :
   `gh run list --workflow=publish-ligne.yml --limit 3`.
   Dernière publication `L104` le 04/09 à 17:42, cadence 11 h → le prochain reel
   est dû vers **04:42 UTC le 05/09**.

2. **Fabriquer `L107` et `L108`** : leurs scripts sont corrigés et leurs moteurs
   écrits. `gh workflow run autoprod-ligne.yml`. Ils complètent la file à trois.

3. **Écrire le lot suivant, à partir de `L109`** — c'est le seul vrai manque.
   Le stock de scripts s'arrête à `L108`.

---

## LES PIÈGES — ce qu'un agent qui reprend perdrait

**`engine` est un NOM NU.** `"engine": "l107"`, jamais un chemin. Le code
construit lui-même `ligne/engine/<engine>.html`. Sans ce champ, ou avec un
chemin, `_engine_path()` renvoie `None` et l'autoprod **saute l'épisode en
silence** — aucune erreur, aucune alerte, la file se vide sans qu'on sache
pourquoi. Livré trois fois de suite en chemin par l'agent d'écriture.

**Le tri de la file est NUMÉRIQUE depuis le 02/09.** En tri de chaînes, `L100`
passe avant `L99` : `L100` est effectivement parti avant `L99`. Corrigé dans
`publish_ligne.py::_oldest_episode`. Le même piège existe partout où on compare
des identifiants d'épisode — ne jamais faire `if ep >= "L98"`.

**Les créneaux planifiés de GitHub sont abandonnés deux fois sur trois.**
Mesuré : 8 déclenchements sur 20 attendus, écart réel médian 5 h pour un cron
réglé à 2 h. Ce n'est pas réparable, seulement compensable en sondant souvent —
c'est pourquoi le sondage est horaire et le court-circuit coûte 7 secondes.

**Trois pannes de paiement en une semaine**, toutes invisibles depuis la chaîne :
GitHub Actions bloqué le 27/08 (facture refusée), ElevenLabs le 02/09 (`HTTP 401
payment_required`, aucune voix générée pendant six heures). Devant une file qui
ne se remplit pas, **regarder les factures avant le code**.

**Le dossier `~/Downloads` est parfois inaccessible** (refus macOS, « Operation
not permitted »), et `ls` le fait passer pour vide au lieu de le dire. Vérifier
avec `ls -la ~/Downloads/fichier.zip` : si le nom s'affiche mais qu'`unzip`
refuse, c'est une autorisation, pas un fichier manquant.

**Une décision qui n'est pas écrite dans le fichier est une décision perdue.**
Le CTA à mot-clé et la phrase-morale ont disparu à chaque fois qu'un lot a
renommé le schéma et supprimé `_rules`. Toute règle se grave dans `_rules` de
chaque épisode ET dans `ligne/AGENT_SCRIPTS.md`.

**Trois refus de build côté carrousel** ont été ajoutés parce que le signalement
ne suffisait pas : couverture en chaîne simple (pas de rouge possible), slide de
fin sans fichier photo, emoji. Un brief fautif ne produit plus rien du tout.

---

## LA DOCTRINE, ET OÙ ELLE VIT

```
ligne/AGENT_SCRIPTS.md        contrat technique, légende en 5 blocs,
                              mécanique contre psychologie, duel ≤ 33 %
ligne/SKILL_LIGNE_MOTEUR.md   la loi complète, dont la LOI 1ter mesurée
carrousel/AGENT_CARROUSEL.md  les deux formats MOFU / BOFU, les interdits
```

Copies prêtes à transmettre : `~/Downloads/GUIDE-REELS/` et
`~/Downloads/GUIDE-CARROUSEL/`.

**Deux mesures à ne pas refaire.** Le segment 3 des trois meilleurs épisodes fait
118 caractères en moyenne contre 252 pour le lot dérivé. Et le duel est le
meilleur archétype — skip médian 44,2 % contre 46,9 % pour l'accusation — donc
son plafond de 33 % est une règle de lassitude, pas de performance : ne pas le
« corriger » en regardant les chiffres.
