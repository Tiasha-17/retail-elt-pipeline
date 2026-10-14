with partner_orders as (
    select * from {{ ref('partner_order_performance') }}
),

portfolio_kpis as (
    select
        count(distinct seller_id) as partner_count,
        count(*) as partner_order_count,
        count(distinct customer_id) as customer_count,
        sum(item_count) as item_count,
        sum(item_revenue) as item_revenue,
        sum(freight_value) as freight_value,
        avg(item_revenue) as average_order_value,
        sum(is_cancelled) / nullif(count(*), 0)::double as cancellation_rate,
        sum(case when is_delivered = 1 then is_late else 0 end)
            / nullif(sum(is_delivered), 0)::double as late_delivery_rate,
        avg(review_score) as average_review_score,
        sum(case when review_score is not null then 1 else 0 end)
            / nullif(count(*), 0)::double as review_coverage_rate
    from partner_orders
),

segment_counts as (
    select
        sum(case when partner_segment = 'Strategic' then 1 else 0 end) as strategic_partner_count,
        sum(case when partner_segment = 'At risk' then 1 else 0 end) as at_risk_partner_count
    from {{ ref('partner_scorecard') }}
)

select *
from portfolio_kpis
cross join segment_counts
