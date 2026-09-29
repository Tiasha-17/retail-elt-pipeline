#!/usr/bin/env python3
"""
Splits the flat Olist CSVs into a simulated monthly landing zone.

Every transactional table (orders, order_items, payments, reviews) is joined
back to orders on order_id and partitioned by the order's purchase month
(order_purchase_timestamp), because none of those tables carry their own
date column that means "when did this batch land". Reference tables
(customers, sellers, products, category translation) are static and land
whole. Geolocation is intentionally excluded — it isn't used by any
star-schema table and it's the single largest file in the dataset.

Usage:
    python partition_landing_zone.py --source /path/to/raw/csvs
"""
import argparse
import csv
import os
import shutil
import sys
from collections import defaultdict

TRANSACTIONAL = {
    "orders": "olist_orders_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "payments": "olist_order_payments_dataset.csv",
    "reviews": "olist_order_reviews_dataset.csv",
}

SEED = {
    "customers": "olist_customers_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "products": "olist_products_dataset.csv",
    "category_translation": "product_category_name_translation.csv",
}


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader), reader.fieldnames


def write_csv(path, fieldnames, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def partition_table(name, filename, source_dir, landing_dir, order_month):
    rows, fields = read_csv(os.path.join(source_dir, filename))
    by_month = defaultdict(list)
    unmatched = 0
    for row in rows:
        month = order_month.get(row["order_id"])
        if month is None:
            unmatched += 1
            continue
        by_month[month].append(row)

    if unmatched:
        print(f"  WARNING: {unmatched} {name} rows had no matching order_id — dropped", file=sys.stderr)

    total_written = 0
    for month in sorted(by_month):
        out_path = os.path.join(landing_dir, name, f"{name}_{month}.csv")
        write_csv(out_path, fields, by_month[month])
        total_written += len(by_month[month])

    assert total_written == len(rows) - unmatched, (
        f"{name}: partitioned row count ({total_written}) does not match "
        f"source row count minus unmatched ({len(rows) - unmatched})"
    )
    print(f"  {name}: {len(rows)} source rows -> {len(by_month)} monthly partitions, "
          f"{total_written} rows written, {unmatched} unmatched")
    return len(rows), total_written


def stage_seed(name, filename, source_dir, seed_dir):
    rows, fields = read_csv(os.path.join(source_dir, filename))
    out_path = os.path.join(seed_dir, f"{name}.csv")
    write_csv(out_path, fields, rows)
    print(f"  {name}: {len(rows)} rows landed whole")
    return len(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, help="Directory containing the raw flat Olist CSVs")
    parser.add_argument("--out", default=os.path.join(os.path.dirname(__file__)),
                         help="Directory under which landing/ and seed/ are created (default: this script's dir)")
    args = parser.parse_args()

    landing_dir = os.path.join(args.out, "landing")
    seed_dir = os.path.join(args.out, "seed")

    if os.path.exists(landing_dir):
        shutil.rmtree(landing_dir)
    if os.path.exists(seed_dir):
        shutil.rmtree(seed_dir)

    print("Loading orders to build order_id -> purchase month map...")
    orders_rows, _ = read_csv(os.path.join(args.source, TRANSACTIONAL["orders"]))
    order_month = {row["order_id"]: row["order_purchase_timestamp"][:7] for row in orders_rows}

    print("\nPartitioning transactional tables by order purchase month...")
    totals = {}
    for name, filename in TRANSACTIONAL.items():
        src_count, written_count = partition_table(name, filename, args.source, landing_dir, order_month)
        totals[name] = (src_count, written_count)

    print("\nLanding reference tables whole...")
    for name, filename in SEED.items():
        stage_seed(name, filename, args.source, seed_dir)

    print("\nVerifying partitioned totals sum back to source totals...")
    for name, (src_count, written_count) in totals.items():
        status = "OK" if written_count == src_count else "MISMATCH"
        print(f"  {name}: source={src_count} written={written_count} [{status}]")
        if written_count != src_count:
            sys.exit(1)

    print("\nLanding zone generated successfully.")


if __name__ == "__main__":
    main()
