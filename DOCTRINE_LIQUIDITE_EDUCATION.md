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

## §L5 — LA FORME : « LA LIGNE CONTINUE » (décidée PO)

**Ce que ce n'est PAS** : pas de facecam, pas de chart annoté façon SMC (= le look des 25
concurrents), pas de personnage récurrent dessiné.

### 1. Le dispositif  *(v2 assouplie — décision PO 2026-07-13)*
**L'axiome n'est PAS « un trait mathématiquement continu ». L'axiome est : JAMAIS DE CUT SEC.**
Chaque changement de scène passe par une **transition fluide** — on prend la moins chère qui reste
soyeuse : morphing quand il est naturel, étirement/glissement d'un élément vers la scène suivante,
sortie-retour du trait, main qui efface/redessine, zoom d'emport, fondu de mouvement.
- **Le morphing intégral (interpolation de path SVG, HyperFrames/GSAP/flubber) = un effet SIGNATURE**,
  réservé aux moments où **la transformation EST l'argument** (l'euphorie qui DEVIENT la chute) — pas
  une contrainte imposée à chaque plan.
- **Test de validation** : regarder l'épisode **sur téléphone**. Si l'œil ne « sort » jamais entre
  deux scènes, c'est conforme. C'est le seul juge — pas la pureté technique du trait.

Une ligne (blanc ou rouge sur noir) reste le véhicule principal, et **les transitions restent
l'argument** quand elles le peuvent : la courbe d'euphorie DEVIENT le trou du drawdown. Inspiration
structurelle *La Linea* (dispositif personnage-sur-ligne + main du créateur — **jamais le design
original, IP protégée**).
- **Casting du trait** : la ligne = le terrain (prix, sol, corde, fusible selon la variable) · la
  main = le pouvoir qui dessine/plie/efface · le petit personnage stylisé = le retail incarné (optionnel).
- **Palette** : N&B + UN rouge. Le chart réel peut apparaître **en citation brève** (preuve, cf. §L3
  formule vérifiable) mais la ligne reste le véhicule principal.

### 2. Le dispositif pédagogique (leçon « C'est pas sorcier »)
- **JAMAIS de concept en titre** — toujours une **énigme concrète** en hook (« pourquoi ton broker
  t'offre la plateforme ? »). Le concept est la réponse.
- **La Ligne = la maquette** : tout mécanisme se **montre en fonctionnement** avant/pendant qu'il se dit.
- **La voix** (clone Patriarche, mais registre différent : pas le mythe — l'**anatomiste**) joue le
  duo : OUVRE avec la question du naïf (l'ignorance légitimée, jamais moquée), RÉPOND en horloger.
- **Ton** : la **fascination froide devant la machine** (« regarde comme c'est bien conçu ») — ni
  indignation, ni cynisme, ni complot.
- **Invariants rituels** : le trait, la main, l'énigme, la révélation (le seg5 = toujours la
  **révélation mécanique**), la règle sèche.

### 3. Règle de réel (complète §L0)
Pas de personnages-vilains dans cette ligne (la Maison / le Troupeau restent dans la saga KONGRAVE).
Des **acteurs réels nommés par catégorie** (banques centrales, desks, brokers B-book, la structure
elle-même) et des **mécanismes documentés**. **Jamais d'accusation nominative d'une entreprise.**
L'arc éditorial : une **enquête sérialisée** — « comment la table est faite » — chaque épisode ferme
sa boucle et rouvre la suivante.

---

> ⚠️ **§L6 et §L7 : extraction sourcée, MAIS la vérification adversariale 3-votes n'a PAS tourné**
> (limite de session, 2026-07-13). Les sources **académiques primaires** citées (Barber-Odean, Odean,
> Kahneman-Tversky, ESMA, arXiv) sont des références *landmark* — fiables. Les **définitions SMC/ICT**
> restent « cadre ». À re-passer en vérification quand le quota le permet.

## §L6 — MANIPULATION & ENTRÉES POST-SWEEP

**Wyckoff = la source mère (doctrine établie).** SMC/ICT en est une réinterprétation.
- **Spring / shakeout** (accumulation) et **Upthrust** (distribution) : casse *brève* sous le support
  (ou au-dessus de la résistance) pour capturer la liquidité, puis **test**, puis repart dans l'autre
  sens — piégeant les vendeurs (ou acheteurs) tardifs. Le **« Composite Man »** (Wyckoff/Pruden) =
  l'opérateur unique qui accumule/distribue = **la main qui plie la ligne**. Cycle de vie :
  accumulation → hausse → distribution → baisse. *C'est ça, la « main » de la ligne continue.*
- **Turtle Soup** (Connors & Raschke, *Street Smarts*, 1995) : fade du **faux breakout** de 20 barres.
  Règles **mécaniques et falsifiables** (nouveau plus-bas 20 j, le précédent ≥ 4 sessions avant, buy
  stop 5-10 ticks au-dessus du plus-bas précédent, stop 1 tick sous le bas du jour). = le rare setup
  SMC-adjacent **vraiment documenté**. **MAIS** le livre ne donne **aucun backtest rigoureux** (exemples
  1995 triés main, discrétionnaire) : règles testables, edge à prouver indépendamment.
- **Judas swing** (ICT, faux mouvement de début de session London/NY), **inducement (IDM)**, **sweep
  vs grab** = **CADRE** (définitions ICT, non mesurées). Le « délibéré » retombe dans le piège d'intention
  du §L0 — à cadrer, jamais asséner.

**Ce qui départage (microstructure établie).**
- Un **backtest walk-forward rigoureux** de signaux microstructure interprétables (mean-reversion +
  breakout) → **pas de significativité** (p = 0,34 ; win rate 46,5 % ≈ pile ou face, p = 0,89, arXiv
  2512.12924). → **le socle d'un edge SMC *systématique* manque. À dire honnêtement.**
- **Résiliency du carnet** (arXiv 1602.00731) : après un gros ordre agressif, spread/profondeur
  reviennent à la moyenne en ~20 updates ; **réversion** domine après un ordre *agressif*, **continuation**
  après un ordre *moins agressif*. → base réelle pour « que fait le prix après un sweep ».

**Entrées post-sweep** (order block strict, FVG/imbalance, OTE 0.62-0.79, breaker/mitigation, MSS/CHoCH
comme confirmation) = **CADRE** : définitions cohérentes mais **sans base empirique/backtest indépendante
consensuelle**. À enseigner comme « le cadre entre ainsi », jamais comme edge prouvé.

## §L7 — PIÈGES & PSYCHOLOGIE (le pont vers LTTI)

**La thèse :** le retail **crée** la liquidité par ses biais. Le stop mis à l'endroit « logique » (sous
le swing low) = là où *tout le monde* le met = le carburant de la cascade (§L1). **La psychologie n'est
pas une faiblesse morale — c'est un design exploité.** Ton : fascination froide devant la machine, jamais
culpabilisant.

- **Disposition effect** (Odean 1998, *Are Investors Reluctant to Realize Their Losses?*) : les
  **gagnants** sont vendus ~50-65 % plus souvent que les perdants. Et les gagnants vendus **surperforment**
  les perdants gardés de **+3,4 %** l'année suivante → couper ses gagnants et garder ses perdants est une
  **erreur mesurée**, pas de la prudence. = le piège « je laisse courir mes pertes ».
- **Overtrading** (Barber & Odean, *Trading Is Hazardous to Your Wealth*, 66 465 comptes) : les plus
  actifs nettent **11,4 %** contre **17,9 %** pour le marché ; l'écart est un effet de **coûts** (net),
  pas de mauvais stock-picking. Mécanisme = **overconfidence**. *Boys Will Be Boys* : les hommes tradent
  **+45 %** (célibataires +67 %), −2,65 pp de rendement.
- **Loss aversion** (Kahneman & Tversky) : λ > 1 **robuste**, MAIS la **magnitude est contestée** (méta-
  analyses : de **1,31 à 2,25** selon la définition — pas un « ×2 » fixe). → formulation honnête : « les
  pertes pèsent plus que les gains — le *combien* varie. »
- **Statistique retail établie** : **74-89 % des comptes CFD perdants** (régulateurs ESMA/AMF) = le chiffre
  citable, contre les chiffres gonflés des prop firms.

## §L4 (mis à jour)
Les trous « manipulation », « profit/entrées » et « pièges & psychologie » sont désormais couverts par
§L6-§L7 (à re-vérifier). Restent ouverts : la **validité hors FX** (crypto/indices) et la **passe
francophone** (source d'étude, priorité basse).

---

*Sources principales : NY Fed Staff Reports 125 & 150 (Osler) ; Equiti, Orbex, Mind Math Money,
Trading Wyckoff, AlgoStorm, FluxCharts, Phidias (pédagogie & taxonomie, secondaires). Recherches
vérifiées 3-votes, juillet 2026.*
*Langue de production : **ENGLISH-FIRST** (cibles anglophones, décision 8/07). Les créateurs
francophones (MaloFX, Bronx, zefrenchtrader, ibrahimchauvin) sont une **source d'étude pédagogique**,
jamais une langue de production ; leur passe reste à faire (priorité basse).*
