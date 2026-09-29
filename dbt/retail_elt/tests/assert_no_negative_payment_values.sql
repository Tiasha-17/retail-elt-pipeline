-- Fails (returns rows) if any payment has a negative value.
-- This is the test the deliberately-injected bad row is designed to trip.
select *
from {{ ref('fact_payments') }}
where payment_value < 0
