# Interview Prep — Retail ELT Pipeline
### A recruiter's judgment of the repo, plus a full walkthrough for interviews

---

## 1. The Recruiter's Verdict

*(An honest read of this repo the way a recruiter or hiring manager actually looks at one — 60-90 seconds, README first, maybe one file click, maybe a CI tab click. Not a technical deep-dive; that's Section 7.)*

### What lands well

- **It's the one repo in the portfolio that actually proves the DE track.** Four other projects (CV classifier, NL2SQL, fraud model, A/B testing tool) all sit on top of a warehouse. This is the only one that builds the thing that fills it — and the README says so in the first paragraph instead of making the reviewer infer it.
- **Every headline claim in this README was actually run, not just written.** `docker compose up`, a real Airflow DAG trigger, per-task state checks, and a query against the resulting DuckDB file all happened in this build — the README's "before rerun: 6512 / after rerun: 6512" and the `PASS=66 ... TOTAL=66` output are pasted from real terminal output, not typed from memory of what it *should* say. That's a genuinely different level of verification than most portfolio READMEs, including some of the other repos in this same portfolio.
- **Two real data-quality findings, not just the one synthetic demo.** Every DE portfolio project injects a bad row and shows a test catching it — that's table stakes, and this repo does it too. What's rarer: profiling the *actual* raw Olist data turned up that `review_id` isn't unique (789 IDs reused across different orders) and that 74 reviews predate their own order's purchase timestamp. Both are modeled explicitly (a composite key, a documented baseline) instead of swept under `distinct` or `coalesce`. That's the difference between "I wrote a test" and "I understand my data."
- **The idempotency claim has a script behind it, not just a sentence.** `tests/test_idempotency.py` loads the same partition twice and asserts the count doesn't move — and the README shows a real run against the full 99,441-row orders table proving it.
- **dbt docs lineage graph is actually embedded**, not described. A reviewer sees the raw → staging → marts → tests flow as a picture without opening a single `.sql` file.

### What a sharp reviewer will flag

- **The idempotency guarantee has a crash-safety gap.** `scripts/load_raw.py`'s `DELETE` and `INSERT` for a partition ([load_raw.py:59-63](scripts/load_raw.py)) are two separate autocommitted statements, not one transaction. Re-running after a *clean* run is provably safe (that's what the test checks) — but if the process dies between the DELETE and the INSERT, that partition is left empty, not duplicated. Idempotent-on-rerun and crash-atomic are different guarantees, and this repo only has the first one. Know this before someone asks "what if it crashes mid-load?"
- **CI never touches Docker or Airflow.** The GitHub Actions workflow runs the loader script and `dbt build` directly against a fixture — real and useful, but it never builds the Docker image, never boots Airflow, never triggers the DAG. The `docker compose up` → DAG-trigger → warehouse-query path in this README was run by hand on one machine, once. A regression in the Dockerfile, the compose file, or a Python import error in the DAG itself would not be caught by CI. Say this yourself if asked "does CI cover the whole pipeline?" — the honest answer is "no, CI covers the transform+test layer; the orchestration layer is manually verified."
- **The Airflow↔dbt integration is the hand-rolled version.** `dbt_build` is a single `BashOperator` shelling out to `dbt build` ([retail_elt_dag.py:60-67](dags/retail_elt_dag.py)) — one Airflow task for the entire dbt run, no per-model retries, no per-model status in the Airflow UI. Production setups increasingly use something like Astronomer's Cosmos, which renders each dbt model as its own Airflow task. Defensible for a demo of this size; be ready to name the tradeoff rather than be caught not knowing the more current pattern exists.
- **The star schema is fully rebuilt every run, not incremental.** All mart models are plain `table` materializations — every `dbt build` re-scans all of `raw.*` and rebuilds `marts.*` from scratch. The build brief explicitly offered this as one of two acceptable patterns (the other being dbt incremental models with a unique key), so this isn't wrong, but it's the simpler of the two options, and it doesn't scale past "small": at 100k rows it's sub-second, at 100M rows it wouldn't be.
- **No completeness signal on the landing zone.** The loader globs `payments_*.csv` and loads whatever matches ([load_raw.py:36](scripts/load_raw.py)) — there's no `_SUCCESS` marker or equivalent to distinguish "file finished landing" from "file is still being written." At this project's scale (a static, pre-generated landing zone) that distinction never comes up, but a real ingestion system needs it, and the brief's own framing ("a batch that either has or hasn't landed yet") implies more rigor than a bare glob provides.
- **One commit.** Same note as the other repos in this portfolio that shipped in one sitting — accurate to how it was built, but if an interviewer looks at `git log` expecting incremental commits the way your earlier Olist/UK Bank repos show, this one won't match that story. Don't lead with "I iterate carefully" using this repo as the example.
- **Default credentials and an exposed webserver config, left in deliberately for local-only use.** `docker-compose.yml` hardcodes `admin`/`admin` and sets `AIRFLOW__WEBSERVER__EXPOSE_CONFIG: "true"`. Completely fine for `docker compose up` on a laptop — actively wrong for anything internet-facing. If asked "is this production-ready as-is," the answer is "no, and here's exactly what I'd change first" (see Section 7), not a pause.
- **No unit tests on the Python loader itself.** `load_raw.py` and `partition_landing_zone.py` are verified end-to-end (the idempotency script, the full local run, the CI fixture) but have no unit tests for edge cases — a malformed CSV, a missing column, an empty partition file. The dbt layer is thoroughly tested; the ingestion code that feeds it is only integration-tested. Worth naming as the next thing you'd add, since another repo in this portfolio (Tool-Using-Agent) has 18 unit tests and this one has zero at the Python level.

### Bottom line

This is the most rigorously *verified* repo in the portfolio — not the most polished, the most verified: every number in the README came from an actual run, including a live Docker/Airflow trigger most portfolio projects only claim works. The two real data-quality findings (non-unique `review_id`, pre-order reviews) are worth more in an interview than the synthetic bad-row demo, because they show you profile data before you model it. The gaps are all in production-hardening (crash atomicity, CI coverage of the orchestration layer, hand-rolled dbt wiring) rather than in correctness — and every one of them is a two-sentence answer if it comes up, not a scramble.

---

## 2. Project Overview

**What is this project?**
A local ELT pipeline: a simulated monthly landing zone of Olist retail CSVs → Airflow loads whichever months have landed into a raw DuckDB schema (idempotently) → dbt transforms raw into a tested star schema (7 models, 51 data tests) → the whole thing runs with one `docker compose up`.

**Why does it matter for interviews?**
It's the fifth project in a portfolio where the other four all build *on top of* a warehouse. This one builds *the pipeline that fills it* — ingestion, orchestration, transformation, and data quality — which is what Data Engineer and Analytics Engineer job descriptions actually ask for, distinct from the Data Analyst/AI Engineer track the other four projects speak to.

**The one-sentence pitch, if asked to explain it in an interview:**
"I built a small but real ELT pipeline — Airflow loads a simulated monthly landing zone into DuckDB idempotently, dbt transforms it into a tested star schema, and I proved both the idempotency and the quality gate actually work by rerunning partitions and injecting a bad row, not just writing tests and hoping."

---

## 3. The Landing Zone and the Idempotent Loader

**What I did:** ([data/partition_landing_zone.py](data/partition_landing_zone.py), [scripts/load_raw.py](scripts/load_raw.py))
The flat Olist CSVs get split into monthly partitions by joining every transactional table back to `orders` on `order_id` and keying on `order_purchase_timestamp` — because none of `order_items`, `payments`, or `reviews` carry their own "when did this land" column. The script asserts partitioned row counts sum back exactly to source totals before exiting successfully (25 monthly partitions for orders/payments/reviews, 24 for order_items — one month had orders but no items yet, which is real, not a bug).

The loader (`load_raw.py`) reads whichever partitions exist and does `DELETE FROM raw.<table> WHERE _partition_month = ?` then `INSERT` for that month — not a blind append — which is what makes reruns safe. A `raw.load_manifest` table records what's landed and when, for observability.

**Interview question you might get:**
*"Walk me through what happens if I run the DAG for the same month twice."*
→ The second run's `DELETE` removes exactly that month's existing rows, the `INSERT` re-adds the same rows from the same file, and the total row count is provably unchanged — that's exactly what `tests/test_idempotency.py` checks and what the README shows against the real 99,441-row orders table (6,512 rows in August 2018 before and after a manual rerun).

**Interview question you might get:**
*"What if the process crashes between the DELETE and the INSERT?"*
→ Honestly: that partition is left empty until the next successful run reloads it. The DELETE and INSERT aren't wrapped in one transaction. I'd fix this by either wrapping both statements in an explicit `BEGIN`/`COMMIT`, or by building the new partition into a staging table and swapping it in with a single atomic `INSERT ... SELECT` — naming this unprompted is a better answer than being asked and not having noticed it.

---

## 4. dbt: Staging, Marts, and the Two Real Data-Quality Findings

**What I did:** ([dbt/retail_elt/models/](dbt/retail_elt/models/))
Eight staging models do one-to-one cleanup of each raw table (type casts, explicit null handling, standardized names). Seven mart models rebuild a star schema — `fact_order_items`, `fact_payments`, `fact_reviews`, `dim_customers`, `dim_products`, `dim_sellers`, `dim_date` — with 51 dbt tests: `unique`/`not_null` on every primary key, `relationships` tests from every fact back to its dimensions, and two custom singular tests.

**The finding that matters most in an interview:** profiling the raw reviews table (99,224 rows) before modeling it showed `review_id` is reused across 789 different `order_id`s — it is *not* a valid primary key in the source data, something you'd only catch by actually counting distinct values instead of assuming a column named `_id` is unique. The composite `(review_id, order_id)` pair is genuinely unique, so [`stg_reviews.sql`](dbt/retail_elt/models/staging/stg_reviews.sql) builds a `review_key` from both and that's what's tested and used as the mart's real primary key.

**The second finding:** 74 reviews have a `review_creation_date` before their order's `order_purchase_timestamp` — mostly (67 of 74) canceled orders, plus a handful of delivered orders with corrupted timestamps upstream. This is pre-existing data debt, not something the pipeline introduced, and it can't be fixed by re-deriving a timestamp that isn't in the source. [`assert_no_review_before_order.sql`](dbt/retail_elt/tests/assert_no_review_before_order.sql) caps it as a documented baseline — the test fails only if the count *grows* past 74.

**Interview question you might get:**
*"Why not just filter out canceled orders to fix that test?"*
→ I checked first: 7 of the 74 anomalies are on `delivered` or `shipped` orders, so filtering by status wouldn't fully explain it, and excluding canceled orders unconditionally would be modeling around the symptom instead of the cause. Capping it as a known, monitored baseline is more honest than either silently dropping rows or leaving the build permanently red over data I can't correct.

**Interview question you might get:**
*"Why is `dim_date` a hardcoded date range instead of derived from the data?"*
→ Fair criticism — `2016-01-01` to `2018-12-31` is a magic constant in [`dim_date.sql`](dbt/retail_elt/models/marts/dim_date.sql). I'd fix it by deriving the bounds from `min()`/`max()` of `stg_orders.order_purchase_date`, with a small buffer, so the date dimension self-adjusts if the landing zone's range changes.

---

## 5. Proving the Quality Gate Is Real

**What I did:** ([scripts/inject_bad_row.py](scripts/inject_bad_row.py))
Appended a payment row with `payment_value = -999.99` to a real landed partition, reloaded it, and re-ran `dbt build`. It failed two tests at once — `assert_no_negative_payment_values` (the intended catch) and `unique_fact_payments_payment_key` (the injected row happened to collide with the payment key of the row it was copied from) — and `dbt build` exited with status 1, which is what fails the Airflow `BashOperator` task and therefore the whole DAG run.

**Interview question you might get:**
*"Why is this convincing evidence instead of just describing the test?"*
→ Because the failure output in the README (`Got 1 result, configured to fail if != 0`, the specific offending row `('b059ee4de278302d550a3035c4cdb740', 1, 'voucher', -999.99)`, and the shell's own `echo $?` → `1`) is what actually happened on a real run, not a description of what the test is supposed to do. Anyone can claim a quality gate; fewer people show the receipt.

---

## 6. Orchestration, Docker, and CI

**What I did:** ([docker-compose.yml](docker-compose.yml), [dags/retail_elt_dag.py](dags/retail_elt_dag.py), [.github/workflows/ci.yml](.github/workflows/ci.yml))
Airflow (LocalExecutor, Postgres metadata DB) and a custom image with `dbt-duckdb` baked in, wired with `docker compose up --build`. The DAG chains five load tasks *sequentially*, not in parallel — a deliberate choice, since DuckDB is a single-writer embedded database and concurrent writes to the same file would corrupt it. `dbt_build` runs last, and `dbt build` (not `dbt run` + `dbt test` as two separate tasks) means a failing test stops the run rather than continuing into a green pipeline with wrong numbers underneath.

CI (GitHub Actions) installs `dbt-core`/`dbt-duckdb` directly, loads a small hand-built fixture (2 orders, 2 customers, one of each dimension) with the same loader script used in production, runs `dbt build` and `dbt docs generate` against it, and uploads the docs as an artifact — all of which I ran locally first to confirm it would actually pass before trusting it in CI.

**Interview question you might get:**
*"Why LocalExecutor instead of Celery/Kubernetes Executor?"*
→ Because the warehouse is a single DuckDB file — a single-writer embedded database — so this pipeline is architecturally bound to one worker process regardless of executor choice. LocalExecutor is the honest choice, not a shortcut: swapping in Celery wouldn't add real parallelism here without also swapping DuckDB for a networked warehouse (Postgres, or a cloud warehouse), which is exactly what's listed under "What I would do next."

**Interview question you might get:**
*"Does your CI prove `docker compose up` works?"*
→ No — and I'd say that unprompted. CI validates the load-and-transform layer against a fixture; the full Docker/Airflow path was verified manually (built the image, brought up the stack, triggered the DAG via the Airflow CLI, confirmed all six tasks succeeded, then queried the resulting warehouse directly to confirm the row counts matched the source exactly). That's real verification, but it isn't automated regression protection — a follow-up CI job that runs `docker compose up` and triggers the DAG in GitHub Actions would close that gap.

---

## 7. Anticipated Interview Questions — Quick Answers

- **"What's the most interesting bug or finding in this project?"** → The `review_id` non-uniqueness (Section 4) — it's a real, upstream data-quality issue that would silently break a naive `unique` test or a naive join, found by profiling before modeling rather than assuming the column name implied the constraint.
- **"Why DuckDB instead of Postgres for the warehouse?"** → Zero setup, zero cloud account, reproducible on any machine including an interviewer's — `docker compose up` and it works. The tradeoff (single-writer, not networked) is named explicitly in Section 6 and in the README's "What I would do next."
- **"What would break first at 100x the data volume?"** → The full-table mart rebuild (Section 4) — every `dbt build` re-scans all of `raw.*`. I'd move to incremental models with a `unique_key` before anything else.
- **"How do you know the pipeline actually ran, not just that you wrote code that should work?"** → Section 1's second bullet — every number in the README, including the Docker/Airflow run, came from a real execution I captured, not a description of expected behavior.
- **"What's missing for this to be production-ready?"** → In order: transactional (not just idempotent) partition loads, default credentials removed, CI exercising the Docker/Airflow layer, and incremental dbt models. All named explicitly in Section 1 rather than discovered by the interviewer.

---

## 8. Quick Reference — Numbers to Have Ready

| Metric | Value |
|---|---|
| Source rows (orders / items / payments / reviews) | 99,441 / 112,650 / 103,886 / 99,224 |
| Monthly partitions (orders/payments/reviews / order_items) | 25 / 24 |
| dbt models (staging + marts) | 15 (8 staging, 7 marts) |
| dbt tests | 66 total (51 data tests + models), 0 failures on clean data |
| Custom singular tests | 2 (negative payments; review-before-order baseline) |
| Non-unique `review_id` collisions found | 789, across 99,224 review rows |
| Review-date anomalies (pre-existing, capped baseline) | 74 |
| Idempotency check | 6,512 rows in August 2018 partition, before and after rerun |
| Bad-row demo result | `dbt build` exit code 1; caught by 2 of the 51 data tests |
| Lines of Python (loader + injector + partitioner + DAG) | ~383 |
| Commits | 1 |
