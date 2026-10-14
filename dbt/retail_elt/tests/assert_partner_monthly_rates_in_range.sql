select *
from {{ ref('partner_monthly_performance') }}
where cancellation_rate not between 0 and 1
   or late_delivery_rate not between 0 and 1
   or review_coverage_rate not between 0 and 1
   or low_review_rate not between 0 and 1
