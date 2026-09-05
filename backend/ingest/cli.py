"""CLI entrypoint for the Garmin Connect data export import pipeline.

Usage:
    python -m backend.ingest.cli --export-dir /path/to/export [options]
"""

import argparse
import logging
import sys

from . import paths
from .loaders.orchestrator import run


def _parse_args(argv):
    parser = argparse.ArgumentParser(description="Import a Garmin Connect data export into Postgres")
    parser.add_argument("--export-dir", required=True, help="Root of the extracted export (contains DI_CONNECT/)")
    parser.add_argument(
        "--categories",
        type=lambda s: s.split(","),
        default=paths.ALL_CATEGORIES,
        help=f"Comma-separated categories to import (default: all - {', '.join(paths.ALL_CATEGORIES)})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse everything and print counts/errors; make zero DB writes (no DB connection needed)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Bypass the import_files unchanged-file skip and re-parse+upsert everything",
    )
    parser.add_argument("--limit", type=int, default=None, help="Process at most N files per category (for fast iteration)")
    return parser.parse_args(argv)


def _print_summary(summary):
    total_files = total_skipped = total_rows = total_errors = total_placeholders = 0
    print(f"\n{'category':<24}{'files':>8}{'skipped':>10}{'rows':>10}{'errors':>10}{'placeholders':>14}")
    for category in sorted(summary):
        s = summary[category]
        print(
            f"{category:<24}{s['files']:>8}{s['skipped']:>10}{s['rows']:>10}{s['errors']:>10}{s['placeholders']:>14}"
        )
        total_files += s["files"]
        total_skipped += s["skipped"]
        total_rows += s["rows"]
        total_errors += s["errors"]
        total_placeholders += s["placeholders"]
    print("-" * 76)
    print(f"{'TOTAL':<24}{total_files:>8}{total_skipped:>10}{total_rows:>10}{total_errors:>10}{total_placeholders:>14}\n")
    return total_errors


def main(argv=None):
    args = _parse_args(argv if argv is not None else sys.argv[1:])

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler("ingest.log"), logging.StreamHandler()],
    )

    unknown = set(args.categories) - set(paths.ALL_CATEGORIES)
    if unknown:
        logging.error(f"Unknown categories: {', '.join(sorted(unknown))}. Valid: {', '.join(paths.ALL_CATEGORIES)}")
        return 1

    logging.info(f"Starting import from {args.export_dir} (categories={args.categories}, dry_run={args.dry_run})")
    summary = run(args.export_dir, args.categories, dry_run=args.dry_run, force=args.force, limit=args.limit)
    total_errors = _print_summary(summary)
    logging.info("Import complete")
    return 1 if total_errors else 0


if __name__ == "__main__":
    sys.exit(main())
