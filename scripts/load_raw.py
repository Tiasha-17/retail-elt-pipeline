#!/usr/bin/env python3
"""
Loads whichever monthly partitions have landed into raw tables in DuckDB.

Idempotent by design: each partition load is DELETE-then-INSERT keyed on
(table, partition_month), so re-running the same month twice never
duplicates rows. A load_manifest table records what's landed and when,
which is also how the DAG can tell "has this batch landed yet" apart from
"already loaded" without re-reading every file on every run.

Usage:
    python load_raw.py --warehouse /data/warehouse/retail.duckdb \
                        --landing /data/landing --seed /data/seed \
                        --table orders   # or: order_items | payments | reviews | seed
"""
import argparse
import glob
import os
import sys

import duckdb

TRANSACTIONAL_TABLES = ["orders", "order_items", "payments", "reviews"]
SEED_TABLES = ["customers", "sellers", "products", "category_translation"]


def ensure_manifest(con):
    con.execute("""
        CREATE SCHEMA IF NOT EXISTS raw;
        CREATE TABLE IF NOT EXISTS raw.load_manifest (
            table_name TEXT,
            partition_key TEXT,
            row_count BIGINT,
            loaded_at TIMESTAMP DEFAULT current_timestamp,
            PRIMARY KEY (table_name, partition_key)
        );
    """)


def load_transactional(con, table, landing_dir):
    pattern = os.path.join(landing_dir, table, f"{table}_*.csv")
    files = sorted(glob.glob(pattern))
    if not files:
        print(f"  no landed partitions found for {table} at {pattern}", file=sys.stderr)
        return

    con.execute(f"""
        CREATE TABLE IF NOT EXISTS raw.{table} AS
        SELECT *, CAST(NULL AS TEXT) AS _partition_month, CAST(NULL AS TIMESTAMP) AS _loaded_at
        FROM read_csv_auto('{files[0]}')
        LIMIT 0;
    """)

    for path in files:
        fname = os.path.basename(path)
        month = fname[len(table) + 1: len(table) + 8]  # YYYY-MM

        con.execute(f"DELETE FROM raw.{table} WHERE _partition_month = ?", [month])
        con.execute(f"""
            INSERT INTO raw.{table}
            SELECT *, '{month}' AS _partition_month, current_timestamp AS _loaded_at
            FROM read_csv_auto('{path}')
        """)
        row_count = con.execute(f"SELECT count(*) FROM raw.{table} WHERE _partition_month = ?", [month]).fetchone()[0]

        con.execute("""
            INSERT INTO raw.load_manifest (table_name, partition_key, row_count, loaded_at)
            VALUES (?, ?, ?, current_timestamp)
            ON CONFLICT (table_name, partition_key)
            DO UPDATE SET row_count = excluded.row_count, loaded_at = excluded.loaded_at
        """, [table, month, row_count])

        print(f"  {table} [{month}]: {row_count} rows (idempotent replace)")

    total = con.execute(f"SELECT count(*) FROM raw.{table}").fetchone()[0]
    print(f"  {table}: {len(files)} partitions loaded, {total} rows in raw.{table}")


def load_seed(con, seed_dir):
    for table in SEED_TABLES:
        path = os.path.join(seed_dir, f"{table}.csv")
        if not os.path.exists(path):
            print(f"  seed file missing: {path}", file=sys.stderr)
            continue

        con.execute(f"""
            CREATE OR REPLACE TABLE raw.{table} AS
            SELECT *, current_timestamp AS _loaded_at
            FROM read_csv_auto('{path}')
        """)
        row_count = con.execute(f"SELECT count(*) FROM raw.{table}").fetchone()[0]

        con.execute("""
            INSERT INTO raw.load_manifest (table_name, partition_key, row_count, loaded_at)
            VALUES (?, 'whole', ?, current_timestamp)
            ON CONFLICT (table_name, partition_key)
            DO UPDATE SET row_count = excluded.row_count, loaded_at = excluded.loaded_at
        """, [table, row_count])
        print(f"  {table}: {row_count} rows (full refresh)")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--warehouse", required=True)
    parser.add_argument("--landing", required=True)
    parser.add_argument("--seed", required=True)
    parser.add_argument("--table", required=True,
                         choices=TRANSACTIONAL_TABLES + ["seed"])
    args = parser.parse_args()

    warehouse_dir = os.path.dirname(args.warehouse)
    if warehouse_dir:
        os.makedirs(warehouse_dir, exist_ok=True)
    con = duckdb.connect(args.warehouse)
    ensure_manifest(con)

    print(f"Loading '{args.table}' into {args.warehouse}")
    if args.table == "seed":
        load_seed(con, args.seed)
    else:
        load_transactional(con, args.table, args.landing)

    con.close()
    print("Done.")


if __name__ == "__main__":
    main()
