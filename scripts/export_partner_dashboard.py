#!/usr/bin/env python3
"""Export dashboard-ready partner analytics tables from the DuckDB warehouse."""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

import duckdb


EXPORT_TABLES = (
    "partner_kpi_summary",
    "partner_monthly_performance",
    "partner_scorecard",
)


def safe_identifier(value: str) -> str:
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value):
        raise ValueError(f"Unsafe SQL identifier: {value!r}")
    return value


def export_table(connection, schema: str, table: str, output_dir: Path) -> int:
    schema = safe_identifier(schema)
    table = safe_identifier(table)
    cursor = connection.execute(f'SELECT * FROM "{schema}"."{table}"')
    columns = [column[0] for column in cursor.description]
    rows = cursor.fetchall()

    output_path = output_dir / f"{table}.csv"
    with output_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(columns)
        writer.writerows(rows)
    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--warehouse", required=True, type=Path)
    parser.add_argument("--schema", default="main_analytics")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/dashboard_exports"),
    )
    args = parser.parse_args()

    if not args.warehouse.exists():
        raise FileNotFoundError(f"Warehouse not found: {args.warehouse}")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    connection = duckdb.connect(str(args.warehouse), read_only=True)
    try:
        for table in EXPORT_TABLES:
            row_count = export_table(connection, args.schema, table, args.output_dir)
            print(f"{table}: {row_count} rows")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
