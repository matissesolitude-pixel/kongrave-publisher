# Étude de système — Morgane Desiré / « DM System Millionaire »

Démontage complet du système d'acquisition, d'offre et de conversion.
Analyse conduite le 3 août 2026, à partir de l'URL d'annonce Instagram payante :
`desire-morgane.com/dm-system-millionaire?utm_medium=paid&utm_source=ig&...`

---

## 0. Note méthodologique — statut probatoire

La policy réseau de l'environnement d'analyse a refusé toute connexion sortante vers
les hosts cibles (`connect_rejected`, 403 au CONNECT). **Aucune page n'a pu être lue
directement.** Le système a été reconstitué par recoupement d'index de recherche :
titres, méta-descriptions, extraits indexés, registres légaux publics.

Trois niveaux de fiabilité sont marqués dans tout le document :

| Marque | Signification |
|---|---|
| **[C]** | Confirmé — présent dans un index ou un registre public |
| **[I]** | Inféré — déduit de la structure, cohérent, non vérifié pièce en main |
| **[?]** | Inconnu — trou à combler par accès direct |

Rien de ce qui suit ne doit être traité comme un chiffre vérifié. Les montants cités
(« 500K », « 10K€/semaine », « des millions générés ») sont des **allégations
marketing**, reprises ici comme objets d'étude, pas comme faits établis. Voir §7.

---

## 1. Cartographie — l'écosystème réel

### 1.1 Entité légale **[C]**

| Champ | Valeur |
|---|---|
| Dénomination | DESIRE MORGANE |
| SIREN / SIRET | 977 819 796 / 97781979600011 |
| Forme | Entrepreneur individuel (EI) |
| Actif depuis | 13/07/2023 |
| Code APE | 7022Z — Conseil pour les affaires et autres conseils de gestion |
| Siège | Vouillé-les-Marais (85450), Vendée |

**Lecture :** structure mono-personne, créée il y a ~3 ans. Une EI **ne publie pas de
comptes**. Il n'existe donc aucun substrat public permettant de corroborer ou d'infirmer
les revendications de chiffre d'affaires. C'est structurel, pas suspect en soi — mais
c'est décisif pour l'analyse de crédibilité (§7).

### 1.2 Surfaces de diffusion **[C]**

| Actif | Adresse | Rôle |
|---|---|---|
| Instagram (actuel) | `@md.desire.morgane` — bio : « pour Coachs & Formateurs » | TOF/MOF principal |
| Instagram (historique) | `@etre.libre.financierement` — « Morgane 🤍 » | Ancien positionnement |
| TikTok | `@morgane.desire` (morgane_dsr) | TOF secondaire |
| YouTube | `@MorganeDesire` | TOF long-format |
| Facebook | page ID `61578053617457` | **Support des ads vidéo** |
| Skool | `dm-systeme-millionaire-7037` — « MD Academie », ~1 000 membres, **gratuit**, privé | MOF / liste possédée |
| Stan.store | `Etrelibrefinancierement` | Vitrine produits |
| Landing 1 | `desire-morgane.com/dm-system-millionaire` | **Cible des ads payantes** |
| Landing 2 | `desire-morgane.com/ma-methode` | VSL → réservation d'appel |

### 1.3 Le pivot — deux ères superposées **[I, forte confiance]**

L'écosystème porte les traces nettes d'un **repositionnement**, les deux couches
coexistant encore :

**Ère 1 — `etre.libre.financierement` / Stan / « 10K€/semaine depuis mon téléphone »**
Avatar large B2C : « devenir libre financièrement ». Marché encombré, faible pouvoir
d'achat, forte défiance.

**Ère 2 — `md.desire.morgane` / « pour Coachs & Formateurs » / DM System Millionaire**
Avatar B2B étroit : des gens qui **ont déjà une offre** et **ont déjà une audience**,
mais ne convertissent pas.

C'est le mouvement le plus intelligent du système, et il est textuellement conforme au
critère **Starving Crowd** : elle a troqué un marché large et pauvre contre un marché
étroit, solvable, en croissance, et — point capital — **adressable par congrégations
identifiables** (elle sait exactement où trouver un coach francophone : dans les DM des
autres coachs).

---

## 2. Le tunnel démonté

### 2.1 Forensique de l'URL fournie **[C]**

```
utm_medium = paid          → campagne payante
utm_source = ig            → Instagram
utm_id / utm_campaign = 120242514477540568   → ID campagne Meta
utm_term              = 120242514477560568   → ID ad set
utm_content           = 120250861625380568   → ID créa (annonce)
fbclid = PAdGRleAT...      → click ID Meta
app_id = 124024574287414   → app Instagram (clic in-app)
```

Deux enseignements :

1. Le préfixe `120…` est un identifiant Meta Ads standard. Campagne et ad set
   partagent la même racine à 20 unités près (`…540568` / `…560568`) : **créés dans le
   même geste**, structure simple — probablement **une campagne, un ad set, N créas**
   testées. La créa (`utm_content`) a une racine différente (`12025086…`) : elle a été
   produite plus tard et injectée dans la structure existante. C'est une signature de
   **rotation créative sur structure stable** — on ne recrée pas la campagne, on change
   la vidéo. C'est exactement la bonne pratique.
2. `app_id` Instagram + `utm_source=ig` : trafic **in-app**, pas navigateur. Le
   prospect ne quitte jamais l'écosystème Meta avant la landing.

### 2.2 Le parcours **[I]**

```
   Reels organiques (IG/TikTok/YT)          Ads vidéo Meta (page FB 61578053617457)
   « la vente de ton offre en ligne… »      « De zéro à 500K en 12 mois (uniquement en DM) »
                │                            « 5000 cas testés, des millions générés »
                │                                          │
                └──────────────┬───────────────────────────┘
                               ▼
              LANDING  /dm-system-millionaire   ou   /ma-methode  (VSL)
                               │
                               ▼
              Skool « MD Academie » (GRATUIT, ~1000 membres)   ←── MOF / liste possédée
                               │
                               ▼
              DM Instagram  ──►  offre payante  [?]
                               │
                               └──►  (piste parallèle) appel 2h, « 20 premières personnes »
```

### 2.3 Ce que fait chaque étage

**TOF — les créas.** Les deux titres d'ads confirmés sont des hooks à structure
identique : *chiffre + délai + mécanisme exclusif entre parenthèses*.
- « De zéro à 500K en 12 mois **(uniquement en DM)** »
- « 5000 cas testés, des millions générés : **la méthode DM qui marche** »

La parenthèse fait tout le travail. Sans elle, c'est un hook revenu banal. Avec elle,
c'est une **revendication de mécanisme** : le lecteur ne se demande plus *combien*, il
se demande *comment est-ce possible sans le reste*. C'est du Hook-Story-Offer où le
hook porte déjà l'offre.

**MOF — le Skool gratuit.** C'est l'organe le plus sous-estimé du système, et le plus
solide. Gratuit, privé, ~1 000 membres. Il ne rapporte rien directement. Il produit
quatre choses :
1. Une **liste possédée**, hors de portée de l'algorithme Instagram.
2. De la **preuve sociale** affichable (« 1k members ») avant tout achat.
3. Un **environnement de chaleur** : le prospect vit dans la communauté pendant les
   ~7 heures de consommation nécessaires avant achat, sans que ça coûte un euro d'ads.
4. **La matière première de la preuve.** La revendication « 5000 cas testés » n'est
   crédible que parce qu'une communauté fournit les cas. Le lead magnet **fabrique
   l'actif de preuve qui vend le lead magnet suivant.** C'est une boucle fermée.

**BOF — le DM.** Le closing se fait dans le canal que l'offre enseigne. Voir §4.

---

## 3. L'offre, passée à l'équation de valeur

> `Valeur = (Dream Outcome × Perceived Likelihood) / (Time Delay × Effort & Sacrifice)`

Promesse officielle **[C]** : *« augmenter son chiffre d'affaires en vendant par DM
Instagram, sans prospection, sans appel »*.

| Terme | Traitement dans son système |
|---|---|
| **Dream Outcome** | CA augmenté. Standard, non différenciant. |
| **Perceived Likelihood** | « 5000 cas testés », « 1k membres », témoignages. Volume plutôt que vérifiabilité. |
| **Time Delay** | « 12 mois » sur le hook, « premiers revenus dès les premières semaines » sur la landing. Compressé. |
| **Effort & Sacrifice** | **← C'EST ICI QUE TOUT SE JOUE.** |

### Le geste central : elle divise le dénominateur

Le marché francophone du high-ticket vend tous la même chose : **setter + closer +
appel découverte**. Tous ces acteurs gonflent le **numérateur** — plus de modules, plus
de bonus, plus de garanties, plus de témoignages.

Elle fait l'inverse. Elle ne promet pas un meilleur résultat. Elle **supprime l'étape
la plus douloureuse du métier** :

> « sans prospection, **sans appel** »

C'est une attaque sur `Effort & Sacrifice`, pas sur `Dream Outcome`. Et
mathématiquement, dans l'équation, diviser le dénominateur est plus puissant que
multiplier le numérateur — parce que le dénominateur tend vers zéro.

**C'est un mouvement de Category of One.** Elle n'a pas cherché à faire des appels
mieux que les autres. Elle a supprimé l'appel. On ne peut pas la comparer à ses
concurrents sur leur axe : elle a changé d'axe.

C'est le seul élément de son système qui mérite d'être copié tel quel — pas dans son
contenu, dans sa **forme de raisonnement**.

---

## 4. Pourquoi ça convertit — la vraie douleur de l'avatar

L'erreur d'analyse serait de croire que « sans appel » est un argument de **confort**.
Ce n'en est pas un. C'est un argument d'**identité**.

L'avatar — coach, formateur, prestataire solo francophone — est très majoritairement
quelqu'un qui :
- a construit une expertise réelle, pas une compétence commerciale ;
- s'est mis à son compte en partie **pour ne pas avoir à vendre** ;
- vit l'appel de vente comme une épreuve, pas comme une tâche ;
- se juge moralement d'être « mauvais en vente », et le vit comme un défaut de caractère.

Pour cette personne, « sans appel » ne dit pas *« tu gagneras du temps »*. Ça dit
**« tu n'es pas obligé de devenir quelqu'un d'autre pour réussir »**.

C'est une **permission**, pas une fonctionnalité. Et une permission ne se compare pas
sur un tableau de features — c'est pour ça que le prix n'a pas besoin d'être justifié
ligne à ligne.

### La congruence méta — l'argument le plus fort du système

Elle vend une méthode de vente par DM. Elle vend **par DM**.
Elle vend « depuis mon téléphone ». Elle le prouve **depuis son téléphone**.

Le mécanisme *est* la preuve. Il n'y a pas d'écart entre la démonstration et la chose
démontrée. Le prospect ne subit pas un argumentaire sur le DM : il **vit** un DM qui
fonctionne sur lui, en temps réel. Au moment où il achète, il a déjà été converti par
la méthode qu'il achète.

C'est structurellement supérieur à un témoignage. Un témoignage demande de croire
quelqu'un d'autre. Ça demande seulement de constater ce qui vient de vous arriver.

---

## 5. Leviers de persuasion — inventaire

| Levier | Mise en œuvre **[C/I]** | Solidité |
|---|---|---|
| **Preuve sociale** | « 1k membres », « 5000 cas testés », témoignages | Volumétrique, **non vérifiable** |
| **Autorité** | Track record personnel auto-rapporté (« de zéro à 500K ») | **Auto-décernée**, aucun tiers |
| **Rareté** | « bonus réservé aux 20 premières personnes qui réservent un appel » **[C]** | **Faible** — non auditable, réinitialisable |
| **Réciprocité** | Skool gratuit, contenu organique dense | **Forte** — valeur réelle donnée d'abord |
| **Cohérence** | Le prospect entre par un DM → il agit déjà selon la méthode | **Forte**, sous-estimée |
| **Sympathie** | Registre personnel, féminin, accessible, « depuis mon téléphone » | **Forte** sur l'avatar |

**Le déséquilibre est net.** Réciprocité et cohérence sont excellemment construites.
Autorité et rareté sont **déclaratives** : rien n'est opposable. Le système tient
debout parce que la chaleur compense l'absence de preuve dure — ce qui fonctionne sur
un avatar B2C-solo, et échouerait immédiatement sur un allocataire institutionnel.

---

## 6. Les deux failles structurelles

### 6.1 La contradiction du canal **[C]**

La landing `/ma-methode` propose **un appel** : *« les 20 premières personnes qui
réservent un appel »*, *« 2 heures qui feront la différence »*.

Elle vend « **sans appel** » — via un tunnel à appel.

Trois lectures possibles :
- **(a)** `/ma-methode` est un **tunnel legacy** de l'ère 1, jamais retiré, encore
  indexé et peut-être encore alimenté en trafic ;
- **(b)** segmentation assumée : DM pour le low/mid-ticket, appel pour le high-ticket ;
- **(c)** « sans appel » s'applique au business **du client**, pas au sien.

Les trois sont défendables. Mais du point de vue du prospect qui voit les deux pages,
**c'est une incohérence visible**, et c'est le point exact où un concurrent frappe.
Une promesse d'affranchissement contredite par le tunnel qui la vend, c'est la fissure
la plus coûteuse du système.

### 6.2 L'empilement de claims sans substrat **[C]**

« 500K en 12 mois », « des millions générés », « 10K€/semaine », « 5000 cas testés ».
Aucun n'est falsifiable. L'EI ne publie pas de comptes — il n'existe donc **aucune voie
publique** de corroboration, ni dans un sens ni dans l'autre.

Ce n'est pas une accusation : c'est une **description de l'architecture probatoire**.
Le système repose entièrement sur la parole du vendeur. Ça fonctionne dans ce marché.
Ça ne survit pas à une audience qui sait lire un track record.

---

## 7. Modèle économique — reconstitution **[I]**

| Étage | Actif | Statut |
|---|---|---|
| Attraction | Reels organiques + ads Meta | **[C]** actif |
| Capture | Skool gratuit, 1k membres | **[C]** gratuit |
| Conversion | DM Instagram | **[C]** canal, **[?]** prix |
| Continuité | ? abonnement / accompagnement | **[?]** |

**Le prix de l'offre payante n'a pas pu être établi.** C'est le trou principal de
cette étude. Par cohérence de marché (coach FR, avatar solo, closing DM sans appel),
la fourchette plausible est **300 € – 2 000 €** en one-shot ou paiement fractionné —
au-delà, le DM seul ne suffit généralement plus à porter la décision, et c'est
précisément pourquoi `/ma-methode` bascule sur un appel. Mais c'est une **inférence de
marché, pas une donnée.**

Structure de coûts quasi nulle : une personne, pas de salariés, delivery numérique,
Skool ~99 $/mois, budget ads variable. La marge brute d'un tel système est mécaniquement
très élevée — ce qui rend les revendications de CA *possibles*, sans les rendre
*vérifiées*.

---

## 8. Transposition — ce qui vaut pour Disruptive, ce qui est à jeter

### 8.1 À prendre — trois choses, et seulement trois

**1. Le raisonnement du dénominateur.**
Ne pas ajouter de valeur : **supprimer la douleur centrale du métier**. La question à
se poser pour Disruptive n'est pas « qu'est-ce qu'on ajoute au programme ». C'est :
*quelle est l'étape que l'avatar redoute le plus, et peut-on l'enlever ?*

Pour le programme d'élite, le candidat évident est le **temps d'écran** : le trader
retail croit que performer exige d'être devant les graphiques toute la journée. Une
promesse construite sur la suppression de cette contrainte — adossée à une méthodologie
de sessions définies (Kill Zones), donc **vraie**, pas déclarative — occupe le même
espace stratégique que son « sans appel », sans en emprunter le vocabulaire.

**2. La communauté gratuite comme liste possédée.**
Elle ne monétise pas son Skool. Elle s'en sert pour sortir de la dépendance
algorithmique, produire de la preuve sociale, et **fabriquer la matière première de ses
case studies**. C'est directement transposable au sourcing de talents pour le fonds :
un espace gratuit où l'on observe des candidats sur la durée est un pipeline de
recrutement déguisé en générosité — et la boucle est honnête, parce que la valeur
donnée est réelle.

**3. La congruence méta.**
Le canal de vente doit être la démonstration du produit. Pour Disruptive : la
communication doit se comporter comme le fonds se comporte. Discipline, absence
d'emballement, drawdown assumé. Si le marketing promet du sang-froid en criant, la
preuve est détruite avant d'être énoncée.

### 8.2 À rejeter — sans discussion

- **Tous les hooks chiffrés sans source opposable.** « 500K en 12 mois », « des millions
  générés ». C'est exactement la classe de claim que la doctrine interdit.
- **La rareté théâtrale.** « Les 20 premières personnes » non auditable. Une fenêtre
  temporelle réelle, oui. Un compteur invérifiable, jamais.
- **L'imagerie « depuis mon téléphone ».** Elle vend l'affranchissement de l'effort.
  Disruptive vend la rigueur. Les deux promesses sont incompatibles.
- **L'autorité auto-décernée.** Elle peut se le permettre : son avatar n'a pas les
  outils pour vérifier. Un allocataire institutionnel, si. Sur ce marché, un claim non
  sourcé ne fait pas zéro — **il fait négatif**.

### 8.3 L'enseignement de fond

Son système est **bien construit sur son axe** : un mécanisme différenciant net, un
avatar précisément défini, un canal congruent, une communauté possédée. La partie
faible n'est pas l'ingénierie — c'est le **substrat probatoire**, entièrement
déclaratif.

C'est précisément l'inverse du problème de Disruptive, qui dispose d'un substrat
réel (track record, infrastructure, cadre réglementaire) et doit apprendre à le
**mettre en tunnel**.

> **La leçon nette : elle a un tunnel excellent sans preuve.
> Disruptive a la preuve sans tunnel excellent.
> Ce qu'il faut lui prendre, c'est l'ingénierie — jamais le discours.**

---

## 9. Zones d'ombre — à combler par accès direct

Ces points **n'ont pas pu être établis** et sont nécessaires pour finir l'étude :

1. **Le prix** de l'offre payante — donnée manquante n°1.
2. **Le contenu exact** des deux landings (structure, VSL, garantie, FAQ, CTA).
3. **La garantie** — existe-t-elle ? satisfait-ou-remboursé, résultat garanti ?
4. **Le mécanisme d'automatisation DM** — ManyChat ? mot-clé déclencheur ? manuel ?
   C'est le cœur opérationnel du produit et il reste opaque.
5. **Le volume publicitaire réel** — nombre de créas actives, ancienneté (Meta Ad
   Library, page `61578053617457`).
6. **La structure d'équipe** — solo ou setters sous-traités ?
7. **Les témoignages** — nombre, nommés/anonymes, chiffrés/qualitatifs.

**Comment les obtenir :** ces sept points se lisent en ~20 minutes depuis un navigateur
personnel — les deux landings, la Meta Ad Library, et une entrée dans le Skool gratuit
suffisent. L'environnement d'analyse ne peut pas le faire à cause de la policy réseau ;
un accès direct le peut.

---

*Étude conduite sur sources publiques indexées uniquement. Aucun accès à un espace privé,
aucune donnée personnelle collectée. Les allégations commerciales citées sont reprises
comme objets d'analyse et ne sont pas validées.*
