# DOCTRINE — REELS ÉDUCATIFS LIQUIDITÉ (ligne "sans le Patriarche")

Base de connaissance + doctrine d'écriture pour une **nouvelle ligne de Reels éducatifs** qui
enseigne la mécanique de la liquidité (SMC/ICT/Wyckoff), distincte de la saga KONGRAVE (le
Patriarche). Issue de deux recherches vérifiées (pédagogie des créateurs + substance liquidité,
juillet 2026). Complète — ne remplace pas — `LTTI_PROFILES.md` (hooks, retain/reward) et
`STYLE_REFERENCE.md`.

---

## §L0 — LA RÈGLE D'OR : ÉTABLI vs CONTESTÉ (garde-fou de crédibilité ET de compliance)

C'est la règle qui doit gouverner CHAQUE Reel liquidité. Elle nous distingue des gourous et nous
couvre côté AMF.

- **ON ENSEIGNE COMME FAIT** ce qui est établi par des sources primaires (données réelles de carnet
  d'ordres) : le regroupement des stops, la cascade, la mécanique de contrepartie (voir §L1).
- **ON PRÉSENTE COMME "CE QUE LE CADRE SMC AFFIRME"** — jamais comme un fait — l'**intention
  délibérée** des institutions de chasser tes stops puis renverser. Formulations à bannir en
  assertion : « les institutions poussent *exprès* le prix vers tes stops », « le sweep sert *à*
  déclencher les stops retail avant de renverser ». **Réfutées en vérification (0-3), largement
  infalsifiables.**
- **Formulation sûre** : « Le prix va souvent chercher la liquidité là où elle est. Que ce soit
  intentionnel ou juste un marché aux enchères qui remplit ses ordres, le résultat pour ton stop
  est le même. » On garde la force pédagogique sans mentir sur la mécanique.
- Jamais de promesse de gain, jamais de chiffre de performance (garde-fou LTTI §4 s'applique ici aussi).

---

## §L1 — LA SUBSTANCE ÉTABLIE (le socle réel, citable)

Source primaire : **Osler / NY Fed Staff Reports 125 & 150** (Journal of Finance 2003, JIMF 2005) —
données réelles de carnet d'ordres d'un grand dealer (~9 655 ordres, ~55 Md$, USD/JPY, GBP/USD,
EUR/USD, 1999-2000).

1. **Où sont les stops (fait mesuré).** Les stop-loss se regroupent **juste au-delà** des chiffres
   ronds : buy stops *au-dessus*, sell stops *en-dessous*. Les take-profit se regroupent *sur* le
   chiffre rond. → Métaphore Reel : *le chiffre rond est un mur ; juste derrière, un champ de mines.*
2. **Le chiffre rond = barrière partiellement réfléchissante.** Le prix tend à rebondir dessus à
   court terme… jusqu'à ce qu'il le franchisse.
3. **La cascade (le vrai moteur du "sweep").** Une fois le niveau franchi, les stops se déclenchent
   **en vagues** : chaque stop devient un ordre marché qui pousse le prix vers le stop suivant →
   **feedback positif auto-renforçant**, mouvements anormalement rapides, sauts de prix. C'est ça,
   mécaniquement, un liquidity sweep. → Métaphore : *dominos*, ou *l'avalanche : une plaque cède,
   tout le versant part.*
4. **La mécanique de contrepartie (le "pourquoi" structurel, établi).** Un stop déclenché = un ordre
   **au marché opposé**. Balayer les stops sous un plus-bas déclenche des ventes (longs piégés +
   shorts de cassure) → ce volume vendeur permet à un gros acteur d'**acheter sans slippage**.
   Symétrique en haut. Un gros ordre a *besoin* d'une réserve d'ordres opposés pour s'exécuter. →
   Métaphore : *pour acheter en gros sans faire exploser le prix, il faut que quelqu'un vende en
   face — et la foule qui se fait stopper, c'est ce vendeur.*
5. **« Running the stops » est un terme documenté** (NY Fed) — mais cadré comme *market lore*
   (pratique nommée), pas comme preuve d'intention systématique. À citer prudemment.

**Limite honnête** : données FX 1999-2000, une banque, 3 paires. Fondateur mais ancien et hors
crypto/indices. Ne pas sur-généraliser.

---

## §L2 — LA TAXONOMIE (vocabulaire du cadre — définitions, pas faits prouvés)

Cohérent sur 6+ sources SMC/ICT, mais **secondaires et auto-référentielles** : à présenter comme
le *vocabulaire* du cadre, utile pour lire un chart, pas comme mécanique de marché prouvée.

- **Liquidité (sens SMC)** = réserve d'**ordres en attente** à niveaux prévisibles (≠ le sens
  standard "facilité d'échange").
- **Buy-Side Liquidity (BSL)** = buy stops **au-dessus des hauts** (stops des vendeurs à découvert +
  ordres de cassure haussière).
- **Sell-Side Liquidity (SSL)** = sell stops **sous les bas** (stops des acheteurs longs + cassure baissière).
- **Où ça se concentre** : swing highs/lows précédents, hauts/bas de session (Asia/London/NY),
  hauts/bas journaliers/hebdo, et **surtout equal highs / equal lows** (deux hauts au même niveau =
  grappe de buy stops ; deux bas = grappe de sell stops). Le double top/bottom du retail EST une
  cible de liquidité.
- **Nuance à ne pas cacher** : un "pool" au-dessus des hauts n'est pas *que* des stops — il mêle
  stops de shorts, ordres de cassure, et take-profits. Dire "surtout des stops" est une simplification.

---

## §L3 — LES PATTERNS PÉDAGOGIQUES (comment enseigner — vérifiés)

Ce qui fait qu'un concept trading "clique". **Beaucoup est déjà dans notre canon** — on réutilise la
colonne vertébrale KONGRAVE en remplaçant le Patriarche par du chart annoté / dataviz.

1. **Métaphore physique = levier n°1.** Rendre l'invisible tangible avec un petit vocabulaire
   d'images répétées : liquidité/FVG = **aimant** (« le marché cherche l'efficience ») ; vide de
   prix = **poche d'air** ; trace institutionnelle = **empreinte / scène de crime**. → C'est notre
   doctrine **seg4 HyperFrames-first** (`STYLE_REFERENCE §E-bis`).
2. **Reframe victime → analyste** = le plus on-brand. *« Tu n'avais pas tort sur la direction — tu
   as juste été transformé en liquidité. »* → c'est le **miroir** LTTI.
3. **Formule vérifiable** : réduire un concept à une règle *checkable* qui sépare le signal du bruit
   (FVG en 3 bougies ; order block strict = 3 conditions). Format court idéal : **énonce la règle →
   montre le cas valide → montre le faux.**
4. **Règle d'or inversée** (virale) : *« Ne cherche pas la cassure, cherche le sweep. »* Punchline
   contre-intuitive.
5. **Concret > abstrait** : nommer les vraies institutions (Goldman, JP Morgan) rend "smart money"
   tangible.
6. **Démystification** (angle viral en soi) : mapper le jargon au classique — order block = zone
   offre/demande, liquidity grab = stop hunt, FVG = gap/imbalance, market structure = tendance Dow /
   support-résistance. La critique n°1 d'ICT = jargon-comme-savoir-caché + surcharge (8 h/concept) ;
   on est l'antidote.
7. **Twin-caption** : analyser le MÊME move en deux vocabulaires (ICT vs SMC) = **littéralement notre
   bulle éditoriale** (deux canaux, un move).
8. **Curiosity loop** : ouvrir une question, la payer à la fin = notre doctrine **RETAIN/REWARD**
   (`LTTI_PROFILES §R`).
9. **Modèle de format = TJR** : un concept, un chart propre, une décision. Simplification radicale,
   psychologie d'abord.

**Structure d'un Reel liquidité (15-30 s)** = HOOK (contre-intuitif ou victime→analyste) → CONCEPT
(1 seule mécanique, métaphore physique) → PREUVE (le chart annoté, le cas valide/faux) → RÈGLE (le
geste, sec — la ligne §L0 tenue).

---

## §L4 — CE QUI RESTE À RECHERCHER AVANT D'ÉCRIRE (trous honnêtes)

Les recherches ont solidement couvert la **taxonomie** (§L2) et le **pourquoi structurel** (§L1).
**Non couverts par des claims vérifiés** — à rechercher séparément avant de faire des Reels dessus :

- **Manipulation (mécanique pas à pas)** : Judas swing (London/NY), turtle soup, inducement (IDM),
  spring & upthrust Wyckoff, fake breakout. → adosser à Wyckoff original.
- **Profit (les entrées après le sweep)** : order blocks, fair value gaps/imbalance, OTE (Fibonacci
  ICT), breaker/mitigation blocks, MSS/CHoCH comme confirmation. → vérifier définition consensuelle
  vs pur narratif.
- **Pièges & psychologie retail** : FOMO au sommet de la liquidité, le stop mis à l'endroit
  "logique" (donc chassé), breakout traps, revenge trading. → adosser à la finance comportementale
  (c'est le pont naturel vers la psychologie KONGRAVE).
- **Validité hors FX 1999-2000** : le clustering Osler tient-il en crypto (24/7, retail) et sur indices ?

---

*Sources principales : NY Fed Staff Reports 125 & 150 (Osler) ; Equiti, Orbex, Mind Math Money,
Trading Wyckoff, AlgoStorm, FluxCharts, Phidias (pédagogie & taxonomie, secondaires). Recherches
vérifiées 3-votes, juillet 2026. Couche francophone (MaloFX, Bronx, zefrenchtrader, ibrahimchauvin)
NON couverte — passe ciblée à faire.*
