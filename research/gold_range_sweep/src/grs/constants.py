"""Constantes figees de l'etude XAUUSD range/sweep.

Tout ce qui est un choix de modelisation est ici, nomme, et modifiable en un
seul endroit. Rien de tout cela ne doit etre duplique ailleurs dans le code.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

# --------------------------------------------------------------------------
# Instrument
# --------------------------------------------------------------------------
SYMBOL = "XAUUSD"

# Dukascopy stocke les prix en entiers. price = raw / DECIMAL_FACTOR.
# XAUUSD chez Dukascopy = 3 decimales => 1000.
DECIMAL_FACTOR = 1000.0

# Un "point" XAUUSD en USD. Convention retenue : 1 point = 0.01 USD.
# Les spreads sont exportes EN POINTS *et* en USD, donc changer cette valeur
# ne detruit aucune information.
POINT = 0.01

# Garde-fou : si le prix median decode sort de cette plage, on s'arrete au lieu
# de re-scaler en silence (un DECIMAL_FACTOR faux doit etre signale, pas devine).
PRICE_SANITY_RANGE = (500.0, 20000.0)

# --------------------------------------------------------------------------
# Parametres de l'etude
# --------------------------------------------------------------------------
# Facteur de projection des cibles : cible_haute = High + k*R, cible_basse = Low - k*R
# Defaut 1.0. Passer a 0.5 = changer cette seule valeur.
PROJECTION_FACTOR = 1.0

BAR_MINUTES = 5

# SWEEP : retour d'une cloture M5 dans le range en N bougies ou moins,
# bougie de franchissement incluse (elle compte comme bougie 1).
SWEEP_MAX_BARS = 3

# BREAKOUT : N clotures M5 consecutives au-dela de la borne, sans retour.
BREAKOUT_CONFIRM_BARS = 3

# Exclusion : trou de donnees dans le RANGE de reference superieur a N minutes.
MAX_RANGE_GAP_MIN = 15

# Profondeur d'historique demandee (mois glissants).
HISTORY_MONTHS = 18

# Seuil plancher de sessions retenues sous lequel il faut elargir l'historique.
MIN_SESSIONS = 120

# --------------------------------------------------------------------------
# MESURE 3 -- choix de modelisation explicites
# --------------------------------------------------------------------------
# Le cahier des charges dit, pour un BREAKOUT, "stop de l'autre cote de la
# borne" sans donner de distance. Une distance nulle serait degeneree (entree
# au retest = sur la borne). On place donc le stop a une fraction de R de
# l'autre cote de la borne franchie. C'est une HYPOTHESE, pas une donnee :
# elle est signalee comme telle dans le rapport.
BREAKOUT_STOP_BUFFER_R = 0.10

# Cout d'execution : la serie de prix est le BID. Un long entre a l'ask et sort
# au bid, un short entre au bid et sort a l'ask => un spread plein par
# aller-retour. Le spread utilise est celui, horodate, de la bougie d'entree.
ROUND_TURN_SPREADS = 1.0

# --------------------------------------------------------------------------
# Criteres d'abandon (ecrits avant tout resultat)
# --------------------------------------------------------------------------
ABANDON_UNCOND_TOUCH_MIN = 0.50    # taux de touche inconditionnel (au moins une cible)
ABANDON_COND_EDGE_MIN = 0.55       # edge conditionnelle
ABANDON_NET_EXPECTANCY_MIN = 0.20  # esperance nette, en R
ABANDON_TOP_DECILE_MAX = 0.40      # part de l'esperance portee par le decile superieur

WILSON_Z = 1.959963984540054  # 95 %

# --------------------------------------------------------------------------
# Ancrages temporels
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class Anchor:
    """Un ancrage temporel.

    Chaque borne est (decalage_de_jour, heure, minute) exprimee dans `tz`,
    relativement a la date de session (= date locale du debut du range).
    """
    name: str
    tz: str
    range_start: tuple[int, int, int]
    range_end: tuple[int, int, int]
    window_end: tuple[int, int, int]
    cutoff: tuple[int, int, int]      # MESURE 1 : "avant 02:30"
    exit: tuple[int, int, int]        # sortie mecanique


ANCRAGE_UTC = Anchor(
    name="ANCRAGE_UTC",
    tz="UTC",
    range_start=(0, 19, 45),
    range_end=(1, 0, 15),
    window_end=(1, 1, 0),
    cutoff=(1, 2, 30),
    exit=(1, 3, 0),
)

# Memes heures a l'horloge de New York. En hiver (EST) elles coincident avec
# ANCRAGE_UTC ; en ete (EDT) elles derivent d'une heure en UTC.
ANCRAGE_NY = Anchor(
    name="ANCRAGE_NY",
    tz="America/New_York",
    range_start=(0, 14, 45),
    range_end=(0, 19, 15),
    window_end=(0, 20, 0),
    cutoff=(0, 21, 30),
    exit=(0, 22, 0),
)

ANCHORS = (ANCRAGE_UTC, ANCRAGE_NY)

# --------------------------------------------------------------------------
# Chemins
# --------------------------------------------------------------------------
ROOT = Path(os.environ.get("GRS_ROOT", Path(__file__).resolve().parents[2]))
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
M5_DIR = DATA_DIR / "m5"
MANIFEST_DIR = RAW_DIR / "_manifest"
EXCLUDED_CSV = DATA_DIR / "excluded.csv"
OUT_DIR = ROOT / "out"
PLOTS_DIR = OUT_DIR / "plots"
SESSIONS_CSV = OUT_DIR / "sessions.csv"
REPORT_MD = OUT_DIR / "report.md"

DUKASCOPY_URL = (
    "https://datafeed.dukascopy.com/datafeed/{symbol}/{year:04d}/{month0:02d}/"
    "{day:02d}/{hour:02d}h_ticks.bi5"
)

# --------------------------------------------------------------------------
# Fermeture hebdomadaire du spot or (UTC). Sert a exclure les week-ends.
# --------------------------------------------------------------------------
WEEKLY_CLOSE = (4, 21, 0)   # vendredi 21:00 UTC
WEEKLY_OPEN = (6, 22, 0)    # dimanche 22:00 UTC

# Depart de la course entre les deux cibles pour la MESURE 2.
# "window_end" = a partir du moment ou la classification est connue.
# "range_end"  = des la fin du range.
COND_RACE_START = "window_end"

HOLIDAY_COUNTRIES = ("US", "CN")
