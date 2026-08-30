"""Ligne de commande.

  python -m grs.cli download [--months 18] [--workers 12] [--force]
  python -m grs.cli aggregate [--force]
  python -m grs.cli sessions
  python -m grs.cli report
  python -m grs.cli all
"""
from __future__ import annotations

import argparse
import sys

from .constants import HISTORY_MONTHS, PROJECTION_FACTOR


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="grs")
    sub = ap.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("download")
    d.add_argument("--months", type=int, default=HISTORY_MONTHS)
    d.add_argument("--workers", type=int, default=12)
    d.add_argument("--force", action="store_true")

    a = sub.add_parser("aggregate")
    a.add_argument("--force", action="store_true")

    for name in ("sessions", "report", "all"):
        p = sub.add_parser(name)
        p.add_argument("-k", "--projection", type=float, default=PROJECTION_FACTOR)
        if name == "all":
            p.add_argument("--months", type=int, default=HISTORY_MONTHS)
            p.add_argument("--workers", type=int, default=12)
            p.add_argument("--skip-download", action="store_true")

    args = ap.parse_args(argv)

    if args.cmd == "download":
        from .download import download_range
        download_range(args.months, workers=args.workers, force=args.force)
        return 0

    if args.cmd == "aggregate":
        from .aggregate import aggregate_all
        aggregate_all(force=args.force)
        return 0

    from .pipeline import class_breakdown, run_report, run_sessions

    if args.cmd == "sessions":
        built, _, _ = run_sessions(k=args.projection)
        print("\nRepartition des classes :")
        print(class_breakdown(built).to_string(index=False))
        return 0

    if args.cmd == "report":
        built, excluded, m5 = run_sessions(k=args.projection)
        run_report(built, excluded, m5)
        return 0

    if args.cmd == "all":
        if not args.skip_download:
            from .download import download_range
            download_range(args.months, workers=args.workers)
        from .aggregate import aggregate_all
        aggregate_all()
        built, excluded, m5 = run_sessions(k=args.projection)
        print("\nRepartition des classes :")
        print(class_breakdown(built).to_string(index=False))
        run_report(built, excluded, m5)
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
