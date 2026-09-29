#!/usr/bin/env python3
"""
Deliberately corrupts one landed partition so the data-quality gate has
something real to catch. Run this, then re-run the pipeline: `dbt build`
should fail on assert_no_negative_payment_values, and the DAG run should
fail with it.

Usage:
    python inject_bad_row.py --landing /data/landing
"""
import argparse
import csv
import glob
import os
import sys


def inject(landing_dir):
    pattern = os.path.join(landing_dir, "payments", "payments_*.csv")
    files = sorted(glob.glob(pattern))
    if not files:
        print(f"No payment partitions found at {pattern}", file=sys.stderr)
        sys.exit(1)

    target = files[-1]
    with open(target, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames

    bad_row = dict(rows[0])
    bad_row["payment_value"] = "-999.99"
    rows.append(bad_row)

    with open(target, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Injected 1 malformed row (payment_value=-999.99) into {target}")
    print("Re-run the load + dbt build to see assert_no_negative_payment_values fail.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--landing", required=True)
    args = parser.parse_args()
    inject(args.landing)
