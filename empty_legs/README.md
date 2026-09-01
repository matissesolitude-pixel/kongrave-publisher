# Cockpit Empty Legs

Veille organisée des vols de repositionnement (empty legs) sur 12 destinations :
Londres, Madrid, Ibiza, Italie, Athènes/Cyclades, Balkans, Lisbonne, Maroc, Dubaï,
Géorgie, Medellín, Iran.

Un empty leg est un vol que l'appareil doit faire à vide pour rejoindre son prochain
client ou regagner sa base. L'opérateur le brade de **-30 % à -75 %** du tarif
d'affrètement. En échange, trois contraintes non négociables :

1. **Ultra-flexibilité** — itinéraire, date et heure sont fixés par le client principal.
2. **Aller simple, appareil entier** — le prix couvre tout l'avion, seul ou à huit.
   En dessous de quatre passagers, comparer systématiquement à un billet business.
3. **Risque d'annulation** — si le client plein tarif décale son vol, votre empty leg
   saute. Le plan B commercial se réserve *avant* de payer.

La fenêtre où tombent les vraies décotes : **24 à 48 h avant décollage**, quand
l'opérateur cherche à amortir son carburant.

## Fichiers

| Fichier | Rôle |
|---|---|
| `destinations.json` | Source de vérité : aéroports (IATA/OACI), densité réelle de l'offre, mois alimentés, jours forts, fourchettes de prix, plan B, notes |
| `plateformes.json` | Les 7 plateformes, leur canal d'alerte, leur coût et la marche à suivre pour configurer |
| `empty_legs.py` | CLI : tableau des routes, fiches de configuration, checklist du jour, tableau de bord HTML |

## Usage

```bash
python empty_legs/empty_legs.py routes                 # tableau des 12 routes
python empty_legs/empty_legs.py routes --mois 12       # se projeter sur décembre
python empty_legs/empty_legs.py alertes                # toutes les fiches de configuration
python empty_legs/empty_legs.py alertes --plateforme xo
python empty_legs/empty_legs.py veille                 # checklist du jour
python empty_legs/empty_legs.py veille --telegram      # même checklist envoyée via notify.py
python empty_legs/empty_legs.py dashboard --out output/empty_legs.html
```

`veille --telegram` réutilise le canal Telegram déjà configuré pour le pipeline
(`TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` dans `.env.local`). Sans ces variables,
l'envoi est un no-op et la checklist reste affichée dans le terminal.

## Mise en place, dans l'ordre

1. **Créer les comptes gratuits** : XO, Victor, PrivateFly, SkyAccess, Welojets.
   `python empty_legs/empty_legs.py alertes` donne la marche à suivre plateforme
   par plateforme et la liste des routes à saisir.
2. **Autoriser les notifications push** au niveau du système sur XO et PrivateFly.
   Une alerte e-mail arrive trop tard sur une offre à -70 %.
3. **Élargir le rayon de départ à 300 km** autour de Paris : Genève, Nice, Bruxelles
   et Luxembourg sont des viviers d'empty legs bien plus fournis que Le Bourget sur
   certaines routes (Grèce, Balkans, Golfe).
4. **Ne pas s'abonner à Jettly tout de suite.** Environ 370 $/mois : à souscrire
   seulement si le rythme dépasse un vol par mois, ou pour couvrir une fenêtre précise
   (Dubaï, Géorgie, Medellín), puis à résilier.
5. **Poser un plafond de prix par route** (colonne « cible empty leg ») pour ne pas
   décrocher sur une offre à -20 % maquillée en bonne affaire.

## Ce que les données disent, et qu'il vaut mieux savoir avant de guetter

- **Londres, Ibiza et l'Italie** concentrent l'essentiel du rendement : flux quotidien,
  retours à vide systématiques, décote réelle de -60 à -75 %.
- **Le Maroc joue en contre-saison** (octobre-avril) : c'est la meilleure fenêtre de
  l'année quand l'Europe se vide.
- **Dubaï** n'est rationnel qu'à partir de 5-6 passagers ; en dessous, la business est
  souvent moins chère que l'empty leg.
- **Medellín depuis l'Europe** est quasi inexistant. La vraie route empty leg est
  Miami/Fort Lauderdale → MDE : ligne jusqu'en Floride, alerte sur le dernier tronçon.
- **La Géorgie** a une densité quasi nulle depuis l'Europe de l'Ouest : poser l'alerte,
  ne rien attendre.
- **L'Iran est hors marché.** Les sanctions internationales visant l'aviation iranienne
  font qu'aucun opérateur ni courtier occidental ne vend cette route, ni plein tarif ni
  empty leg. Aucune alerte à configurer ; toute offre qui apparaîtrait sur cette route
  est un signal d'alerte, pas une bonne affaire.

## Limites assumées

Les fourchettes de prix sont **indicatives** (marché 2025-2026) et servent de seuil de
décision, pas de devis : le prix affiché par l'opérateur fait foi. Les plateformes font
évoluer leurs tarifs d'abonnement et leur couverture — revérifier à l'inscription. Le
script n'interroge aucune API et ne réserve rien : il produit la configuration de la
veille, les alertes des plateformes font le reste.
