"""Auto-test bout en bout du pipeline sur des ticks SYNTHETIQUES.

But : prouver que la chaine tourne, pas produire un resultat de marche.
Ecrit dans un repertoire jetable, jamais dans out/ ni data/.
"""
import os, pathlib, shutil, sys, tempfile

ROOT = pathlib.Path(tempfile.mkdtemp(prefix="grs-selftest-"))
os.environ["GRS_ROOT"] = str(ROOT)
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from grs import constants as C            # noqa: E402
from grs.aggregate import aggregate_all   # noqa: E402
from grs.download import validate_ticks   # noqa: E402
from grs.pipeline import class_breakdown, run_report, run_sessions  # noqa: E402
from grs.synthetic import make_ticks, write_raw  # noqa: E402

print(f"racine jetable : {ROOT}\n")
print("== 1. ticks synthetiques ==")
ticks = make_ticks(n_days=int(os.environ.get("SELFTEST_DAYS", 200)),
                   vol_scale=float(os.environ.get("SELFTEST_VOL", 1.0)))
validate_ticks(ticks)
print(f"{len(ticks):,} ticks  {ticks['ts'].min()} -> {ticks['ts'].max()}")
print(f"spread median {(ticks['ask'] - ticks['bid']).median() / C.POINT:.1f} points")
parts = write_raw(ticks, C.RAW_DIR)
print(f"{len(parts)} partitions mensuelles ecrites dans data/raw/\n")

print("== 2. agregation M5 ==")
m5 = aggregate_all()
print(m5.head(3).to_string(index=False))
print()

print("== 3. sessions ==")
built, excluded, m5 = run_sessions()
print("\nRepartition des classes :")
print(class_breakdown(built).to_string(index=False))
print()

print("== 4. rapport ==")
run_report(built, excluded, m5,
           note="> **Donnees SYNTHETIQUES** : auto-test de plomberie. "
                "Aucun chiffre de ce document n'a de signification de marche.")

print("\n== fichiers produits ==")
for p in sorted(ROOT.rglob("*")):
    if p.is_file():
        print(f"  {p.relative_to(ROOT)}  ({p.stat().st_size:,} o)")

keep = os.environ.get("SELFTEST_KEEP")
if keep:
    shutil.copytree(ROOT, keep, dirs_exist_ok=True)
    print(f"\ncopie conservee dans {keep}")
else:
    shutil.rmtree(ROOT, ignore_errors=True)
