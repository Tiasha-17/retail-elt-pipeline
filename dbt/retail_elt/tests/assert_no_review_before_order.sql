-- The raw Olist export has 74 pre-existing rows where review_creation_date
-- predates the order's purchase timestamp (mostly canceled orders, plus a
-- handful of delivered orders with corrupted timestamps upstream -- see
-- README "Data quality" section for the profiling that found this). That's
-- upstream data debt this pipeline didn't introduce and can't fix by
-- re-deriving a truth that isn't in the source, so it's capped as a known
-- baseline instead of silently ignored: the test fails if the count ever
-- grows past 74. (The deliberately-injected bad-row demo in this repo
-- targets assert_no_negative_payment_values instead, since a payment sign
-- error is unambiguously wrong in a way a timestamp order isn't.)
with anomalies as (
    select *
    from {{ ref('fact_reviews') }}
    where review_creation_at < order_date
)

select count(*) as anomaly_count
from anomalies
having count(*) > 74
