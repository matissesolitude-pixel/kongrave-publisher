# Reel quotidien DCT (War Room)

## La file

Un Reel prêt = UN sous-dossier de `dct/queue/` nommé `AAAA-MM-JJ-<sujet>`, contenant
UN `.mp4` et un `caption.txt`. Le workflow prend le plus ancien, publie, puis archive
dans `dct/published/` sans le master.

## L'heure

20h15 à Paris. Le cron tourne à 18h15 ET 19h15 UTC pour couvrir les deux états de
l'heure d'été ; `publish_dct.py` tranche sur l'heure réelle de Paris, donc un seul des
deux runs publie.

## L'encodage

`publish_dct.py` renormalise toujours avant l'envoi : H.264 High 4.0, yuv420p, 30 i/s,
GOP fermé, AAC LC 44,1 kHz MONO, moov en tête. C'est le profil que ce compte a déjà fait
accepter. Un master en 48 kHz stéréo a été refusé le 27/10 par un `ProcessingFailedError`
opaque. Ne pas changer ce profil sans une preuve de publication.

## Les descriptions (règles de M, 27/10/2026)

**Instagram.** La première ligne annonce le lien en bio vers la War Room. Rien avant.
La description reste COURTE : M a refusé une version de dix lignes le 27/10. Deux
paragraphes maximum, puis les hashtags.

**YouTube Short.** Pas de lien Skool. La description met en avant la CHAÎNE YouTube :
le premier mot demande l'abonnement. Le titre doit accrocher, pas décrire ; une phrase
descriptive du genre « We set three targets before the session and price reached all
three » a été refusée le 27/10.

**TikTok.** Le compte @dumbcircletraders n'a PAS de lien en bio et n'en aura pas avant
1 000 abonnés, limite de TikTok. On écrit donc l'adresse en clair dans la description,
`skool.com/dct`, et jamais « link in bio », qui serait faux.

## Les comptes

| Réseau | Compte | Comment on publie |
|---|---|---|
| Instagram | celui du secret `INSTAGRAM_BUSINESS_ACCOUNT_ID` | ce workflow, automatique |
| YouTube | chaîne Dumb Circle Traders `UCoA-fnWeaGGMMfXwEbqppNg` | à la main dans Studio |
| TikTok | `@dumbcircletraders` | à la main dans TikTok Studio |

YouTube et TikTok n'ont aucun identifiant d'API dans ce dépôt. Tant qu'ils n'y sont pas,
ces deux-là passent par le navigateur déjà connecté.
