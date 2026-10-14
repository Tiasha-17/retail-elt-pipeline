with source_total as (
    select round(sum(price), 2) as item_revenue
    from {{ ref('fact_order_items') }}
),

partner_total as (
    select round(sum(item_revenue), 2) as item_revenue
    from {{ ref('partner_order_performance') }}
)

select
    source_total.item_revenue as source_revenue,
    partner_total.item_revenue as partner_revenue
from source_total
cross join partner_total
where abs(source_total.item_revenue - partner_total.item_revenue) > 0.01
