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
Mais la **continuité du trait reste le DÉFAUT** : on la garde chaque fois qu'elle est naturelle. Les
transitions douces alternatives sont une **soupape** — activée quand le morphing pur devient coûteux,
**jamais un choix de confort**.
- **Ordre de préférence strict** : `morphing continu (path SVG)` **>** `transition douce`
  **>** *(cut sec = INTERDIT)*. On ne descend d'un cran que si le cran du dessus n'est pas raisonnablement
  atteignable sur ce plan.
- **Transitions douces admises (la soupape)** : étirement/glissement d'un élément vers la scène
  suivante, sortie-retour du trait, main qui efface/redessine, zoom d'emport, fondu de mouvement.
- **Le morphing intégral (interpolation de path SVG, HyperFrames/GSAP/flubber)** reste **l'effet
  SIGNATURE** aux moments où **la transformation EST l'argument** (l'euphorie qui DEVIENT la chute) — là
  il est obligatoire, pas optionnel.
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
- **AUCUN générique** *(décision PO 2026-07-13, gravée)* — contrairement à la saga KONGRAVE, la Ligne
  n'a PAS de générique de fin. L'épisode se termine sur la dernière scène (la règle + la micro-pulsation
  de la ligne) ; la **boucle Instagram ramène directement à l'énigme d'ouverture**. L'énigme d'ouverture
  EST la signature de la Ligne — pas un logo.
- **CANON VOIX** *(décision PO 2026-07-13, gravée)* — la Ligne quitte le clone Patriarche : **voix Ligne =
  `George` (premade ElevenLabs UK, voice_id `JBFqnCBsd6RMkjVDRZzb`)**, registre enseignant passionné /
  conteur documentaire. **Saga KONGRAVE = clone Patriarche `5wFwpkZR2Yf6aS6EXd8M`. The Week = clone
  Patriarche.** La Ligne est un format 100 % autonome — seul le compte Instagram les relie.
- **DA v3 « CLARTÉ D'ABORD »** *(décision PO 2026-07-13)* — la clarté EST la DA. Motion 2D flat pédagogique,
  **fond CLAIR** (papier chaud), couleur **fonctionnelle** (max 2 désaturées/scène : ton flux vs le leur),
  **labels courts dans le schéma** (YOUR ORDER, THEIR BOOK…), **plus aucun burst ni caption jaune**. Test
  de validation : chaque scène **muette** doit se comprendre. Palette + conventions : `ligne/DA_LIGNE.md`.

### 3. Règle de réel (complète §L0)
Pas de personnages-vilains dans cette ligne (la Maison / le Troupeau restent dans la saga KONGRAVE).
Des **acteurs réels nommés par catégorie** (banques centrales, desks, brokers B-book, la structure
elle-même) et des **mécanismes documentés**. **Jamais d'accusation nominative d'une entreprise.**
L'arc éditorial : une **enquête sérialisée** — « comment la table est faite » — chaque épisode ferme
sa boucle et rouvre la suivante.

## §L5.2 — DOCTRINE VISUELLE & TECHNIQUE (gravée, validée L1, vaut L2-L11)

*DA « Clarté d'abord » + moteur de production. Référence détaillée : `ligne/DA_LIGNE.md`.*

- **Fond CLAIR** (papier `#F2EFE7`), **2D flat pédagogique**, trait encre `#20242A` épais (~10px), centrage axe médian x=540.
- **Couleur FONCTIONNELLE, max 2/scène** : `--you #1E5F6E` (toi / ton flux) vs `--them #8A5323` (eux / le broker / leur livre). Désaturées, **constantes entre épisodes** (jamais inverser la sémantique).
- **Labels courts DANS le schéma** (YOUR ORDER, THEIR BOOK, 10 ACCOUNTS…), gros/gras/contrastés, en **zones réservées** — contrôle de collision : **aucune ligne ne traverse un texte, deux éléments ne se dessinent jamais l'un sur l'autre**.
- **PAS de burst / mot-choc, PAS de caption jaune saga, PAS de générique** (fin sur la règle, la boucle IG ramène à l'énigme = signature).
- **Voix = George** (premade ElevenLabs UK `JBFqnCBsd6RMkjVDRZzb`, enseignant passionné), speed 1.12.
- **SYNC MOT-À-MOT OBLIGATOIRE** : chaque texte/élément apparaît sur le mot exact prononcé (timestamps ElevenLabs `with-timestamps` → `words.json`, helper `wt()`). Jamais des fractions de scène. L'écran n'est jamais vide au démarrage.
- **RÈGLE ABSOLUE — ZÉRO FRAME MORTE** : *tant que la voix parle, quelque chose se construit, se transforme, respire ou se déplace.* Trous comblés par : avancer l'élément suivant, faire vivre l'élément présent (`breathe`/`drift` — respiration/dérive lente, amplitude faible), étaler le tracé, ou un mouvement de sens (le prix qui évolue, le point qui avance). **Jamais de remplissage gratuit** : le mouvement sert le propos. **Corollaire (transformation) :** quand un élément doit se transformer, la **transformation elle-même occupe la fenêtre de voix** (grossir→segmenter→tomber, étalé) — on ne fait jamais patienter un élément avec un mouvement décoratif avant de le transformer d'un coup. Audit : passer la timeline au crible (diff pixel frame-à-frame croisé aux fenêtres de voix).
## §L5.5-LAVOISIER — RIEN NE SE PERD, RIEN NE SE CRÉE, TOUT SE TRANSFORME (canon, cœur du format, gravé 2026-07-14)

*Remplace toutes les règles antérieures de transition et de continuité. C'est le cœur de la Ligne.*

**RÈGLE ABSOLUE : aucun élément n'apparaît de nulle part, aucun ne disparaît dans le vide.** Toute matière vient de quelque chose et devient quelque chose.
1. **NAISSANCE** — un élément arrive TOUJOURS de quelque part : il se détache d'un autre (le point du `?` devient la balle) · se dessine depuis un ancrage existant · entre par le bord du cadre · **sort de la balle-pivot**. INTERDIT : fade-in ex nihilo, pop, scale-depuis-zéro au milieu du vide.
2. **MORT** — un élément part TOUJOURS quelque part : il se **rétracte dans la balle** · se transforme en l'élément suivant · sort par le bord · **tombe avec physique** (détruit, pas effacé). INTERDIT : fade-out, `autoAlpha:0` sans destination.
3. **LA BALLE-PIVOT = le réservoir de matière** — née du point du `?` au hook, elle **absorbe** les éléments en fin de scène, les **redéploie** au début de la suivante, et vit jusqu'à la dernière image. **Elle EST le prix**, l'acteur permanent de tous les mécanismes (roule sur la courbe, déclenche les stops, se fait piéger, repart). Implémentée au DRIVER (`collapse`/`deploy` génériques), pas dans chaque archétype.
4. **CONSÉQUENCE** — un épisode = **UN SEUL PLAN-SÉQUENCE** de matière continue. Aucun cut, aucun écran vide, aucune apparition arbitraire. Le spectateur suit un flux, il ne se réoriente jamais.

**Moteur pivot** : `ligne/engine/index_pivot.html` (L3+). L1/L2 gardent `index.html` (figés). Si validé, devient le moteur standard.

## §L5.5 — LA VIE EST NARRATIVE, PAS DÉCORATIVE (canon, gravé 2026-07-13)

- **À chaque instant, l'image AVANCE** : quelque chose se construit, se transforme, progresse vers son but, ou révèle. **INTERDIT** : oscillation / pulsation / dérive / respiration d'un objet statique utilisée comme remplissage (= frame morte déguisée).
- **Combler une fenêtre de voix, par ordre** : 1. ÉTALER la construction (l'action primaire occupe toute la fenêtre) · 2. AVANCER (le prix monte vers le niveau, la foule converge, la cascade se propage — le mouvement EST le propos) · 3. ANTICIPER (la scène suivante commence 0,3-0,5s avant la fin de la précédente) · 4. ENRICHIR (un détail se précise). Si aucune ne remplit → **le copy est trop long, on le réécrit.**
- **Nuance — pause tolérée** : une pause **intentionnelle et courte (≤1,5s)** est autorisée (avant une révélation, sur un silence, à la fin d'une démo — le temps que l'image « prenne ») ; un mouvement doux y est admis (suspension, pas vide). **Interdit** : la respiration comme remplissage sur une longue fenêtre faute d'idée.
- **LE SCANNER EST UN TEST (fail-loud)** : `build_ligne.py` scanne les fenêtres de voix après rendu ; **>1,5s sans progression → le build ÉCHOUE** avec la liste. La doctrine n'est pas une consigne, c'est un gate. *(Limite connue : le scanner pixel ne « voit » pas l'avance lente d'un petit élément — les éléments qui avancent doivent laisser une traînée dessinée / être assez visibles.)*
- **CONTINUITÉ DE MATIÈRE — jamais d'écran vide** : à aucun moment, entre aucune scène, l'écran n'est vide. Un élément de la scène N **devient** un élément de la scène N+1 (le `?` devient la balle / le niveau / le premier trait). Si aucune transformation n'est naturelle, la scène N+1 **commence à se construire AVANT** que la N finisse (chevauchement). Le scanner échoue aussi sur les **écrans quasi-vides** (<0,4% d'encre pendant la voix).
- **PHYSIQUE — easings mous BANNIS partout** : un objet lourd tombe vite (`power4.in`/gravité), un objet qui frappe **rebondit** (`bounce.out` — rebonds décroissants, timing qui se resserre), un objet qui balaie **ne saccade pas** (fauchage continu, les éléments tombent dans son sillage). Rythme balle : chute brutale → rebonds → attaque continue.
- **SCÈNE FINALE UNIQUE** : la clôture d'un épisode **ne réutilise JAMAIS la forme du précédent** (le `fork` reste au catalogue mais pas deux fois de suite). Sa forme découle de la RÈGLE de l'épisode. Ex. brique **`replay`** : on rejoue le mécanisme avec le bon geste, le résultat change (démonstration, pas énoncé).

## §L5.4 — RÉPARTITION MOTEUR / JSON (canon, gravé 2026-07-13)

- **MOTEUR** (`ligne/engine/` + `build_ligne.py`) = tout ce qui est **COMMUN et INVARIANT** : centrage, zones réservées, sync mot-à-mot, zéro frame morte, palette, typo, épaisseurs, rythme de tracé, transitions, filigrane, safe zones — **toute l'esthétique**. Un changement ici s'applique **rétroactivement à TOUS les épisodes**.
- **JSON** (`ligne/episodes/<id>.json`) = ce qui est **PROPRE à l'épisode** : le copy (voix), la séquence, les paramètres de scènes (labels, n…), les **mots-déclencheurs** (sync). Plus la **SPEC d'une brique neuve** (uniquement la première fois, section `SPECS_BRIQUES_NEUVES`).
- Une brique neuve, une fois codée, **REJOINT le moteur** : les épisodes suivants l'invoquent par son **nom**, sans jamais la redécrire.
- **Le JSON ne contient JAMAIS de couleur, position, timing, taille.** Tout réglage esthétique va dans le moteur, jamais dans l'épisode.
- **Catalogue d'archétypes (10)** : hook · routing · mirror · count · faceoff · fork (socle L1) + **crowd · cluster · cascade · aftermath** (ajoutés L2 ; cascade = mécanisme central, resservira). À venir : doors · scale · zoom · gap · merge · stack · coin (cible 15-20).

## §L5.3 — VARIÉTÉ & DURÉE (canon, gravé 2026-07-13)

- **Nombre & ordre de scènes LIBRES** (4 à 8 scènes) : la structure suit le **copywriting**, jamais l'inverse. Le moteur (`ligne/engine/`) accepte N scènes dans n'importe quel ordre d'archétypes.
- **Jamais deux épisodes CONSÉCUTIFS avec la même SÉQUENCE d'archétypes.** (À vérifier à chaque nouvel épisode contre le précédent.)
- **La bibliothèque doit GROSSIR** — cible **15-20 archétypes**. Chaque épisode qui exige une forme neuve l'**ajoute au catalogue** (nouvel archétype dans le moteur). **Ne jamais forcer un contenu dans une brique existante** — le signaler et créer la brique. Archétypes actuels (6) : hook · routing · mirror · count · faceoff · fork.
- **Durée LIBRE (45s à 90s+)**, dictée par la matière — jamais par un gabarit. Un épisode simple boucle court ; une enquête à étages prend le temps qu'il faut. **Test de coupe** : chaque tranche doit contenir un **étage de révélation** ; si on peut retirer 15s sans perdre un étage, on les retire.

- **Moteur** : HyperFrames 0.7.56 (`PRODUCER_FORCE_SCREENSHOT=true`), GSAP + reveals via `tl.set()` dans le temps (jamais `gsap.set` au parse → points parasites). 1080×1920, 30fps.

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
