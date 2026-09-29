#!/usr/bin/env python3
"""
Proves the "rerunning the same month twice doesn't duplicate rows" claim
instead of just asserting it in the README. Loads the fixture landing zone
twice into a scratch DuckDB file and fails if any raw table's row count
changes between the two loads.

Usage:
    python tests/test_idempotency.py
"""
import subprocess
import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
WAREHOUSE = ROOT / "tests" / "idempotency_check.duckdb"
LANDING = ROOT / "tests" / "fixtures" / "landing"
SEED = ROOT / "tests" / "fixtures" / "seed"
TABLES = ["orders", "order_items", "payments", "reviews", "seed"]


def load_all():
    for table in TABLES:
        subprocess.run(
            [
                sys.executable, str(ROOT / "scripts" / "load_raw.py"),
                "--warehouse", str(WAREHOUSE),
                "--landing", str(LANDING),
                "--seed", str(SEED),
                "--table", table,
            ],
            check=True,
        )


def counts():
    con = duckdb.connect(str(WAREHOUSE))
    result = {}
    for table in ["orders", "order_items", "payments", "reviews",
                  "customers", "sellers", "products", "category_translation"]:
        result[table] = con.execute(f"SELECT count(*) FROM raw.{table}").fetchone()[0]
    con.close()
    return result


def main():
    if WAREHOUSE.exists():
        WAREHOUSE.unlink()

    print("First load...")
    load_all()
    first = counts()
    print(f"  row counts: {first}")

    print("Second load (same partitions, must not duplicate)...")
    load_all()
    second = counts()
    print(f"  row counts: {second}")

    if first != second:
        print(f"IDEMPOTENCY FAILURE: counts changed on rerun\n  before={first}\n  after={second}",
              file=sys.stderr)
        sys.exit(1)

    print("Idempotency confirmed: row counts unchanged after rerunning the same partitions.")
    WAREHOUSE.unlink()


if __name__ == "__main__":
    main()
