# Partner analytics metric dictionary

The analytics layer treats a seller as the marketplace partner. Its core grain is
one seller-order relationship because one customer order can contain items from
multiple sellers. This prevents item revenue from being duplicated while still
allowing each partner's operational performance to be measured.

## Commercial metrics

| Metric | Definition | Primary model | Important caveat |
| --- | --- | --- | --- |
| Item revenue | Sum of item price before freight | `partner_order_performance` | This is gross merchandise value, not company revenue or margin |
| Customer value | Item revenue plus freight value | `partner_order_performance` | Payment totals can differ because of vouchers and split payments |
| Average order value | Mean item revenue at the seller-order grain | Monthly and lifetime scorecards | This is partner-order value, not whole marketplace-order value |
| Revenue growth rate | Current partner-month revenue minus previous observed month, divided by previous observed month | `partner_monthly_performance` | Missing months are not filled; this compares active months |
| Customer count | Distinct source customer IDs served by the partner | Monthly and lifetime scorecards | The source creates a customer ID per order; it is not lifetime customer identity |

## Operational and experience metrics

| Metric | Definition | Denominator | Important caveat |
| --- | --- | --- | --- |
| Cancellation rate | Cancelled or unavailable partner-orders | All partner-orders | Multi-partner orders contribute once per participating seller |
| Late-delivery rate | Delivered partner-orders received after the promised date | Delivered partner-orders | The source has no carrier or route dimension for root-cause attribution |
| Average review score | Mean order-level review score linked to the partner-order | Reviewed partner-orders | An order review is shared across every seller on a multi-seller order |
| Review coverage rate | Partner-orders with a review | All partner-orders | Low coverage should reduce confidence in the average score |
| Low-review rate | Reviewed partner-orders scoring 1 or 2 | Reviewed partner-orders | Descriptive signal only; it does not identify the cause of dissatisfaction |

## Partner segmentation

`partner_scorecard` uses portfolio-relative benchmarks so the segments adjust to
the data rather than claiming universal thresholds:

- **At risk:** at least five partner-orders and cancellation, late delivery or
  review performance worse than the relevant portfolio quartile.
- **Strategic:** item revenue at or above the portfolio's 80th percentile and not
  already classified as at risk.
- **Growth opportunity:** order count at or above the median and average review
  score of at least 4.0.
- **Monitor:** every remaining partner, including low-volume partners with too
  little evidence for an operational intervention.

These labels support prioritisation, not automated enforcement. A partner manager
should review sample size, category mix and local operating context before acting.
