# Data

This project doesn't commit any data — `data/landing/`, `data/seed/`, and
`data/warehouse/` are all gitignored. Everything is regenerable.

## 1. Get the raw source

Download the [Olist Brazilian E-Commerce dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)
from Kaggle and unzip it somewhere, e.g. `~/raw-olist/`.

## 2. Build the simulated landing zone

```bash
python3 data/partition_landing_zone.py --source ~/raw-olist
```

This splits `orders`, `order_items`, `payments`, and `reviews` into monthly
partitions (joined back to `orders` on `order_id`, keyed by
`order_purchase_timestamp`) under `data/landing/<table>/<table>_YYYY-MM.csv`,
and lands `customers`, `sellers`, `products`, and the category-translation
table whole under `data/seed/`. Geolocation is intentionally excluded — it's
59MB and unused by any star-schema table.

The script asserts that every partitioned table's row count sums back
exactly to its source total before it exits successfully, so a silent
row-loss bug in the split can't slip through.

## 3. Run the pipeline

See the top-level [README](../README.md) for `docker compose up`.
