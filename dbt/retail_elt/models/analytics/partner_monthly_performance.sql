with partner_orders as (
    select * from {{ ref('partner_order_performance') }}
),

sellers as (
    select * from {{ ref('dim_sellers') }}
),

monthly as (
    select
        po.seller_id,
        po.order_month,
        s.seller_city,
        s.seller_state,
        count(*) as order_count,
        count(distinct po.customer_id) as customer_count,
        sum(po.item_count) as item_count,
        sum(po.item_revenue) as item_revenue,
        sum(po.freight_value) as freight_value,
        sum(po.customer_value) as customer_value,
        avg(po.item_revenue) as average_order_value,
        sum(po.is_delivered) as delivered_orders,
        sum(po.is_cancelled) as cancelled_orders,
        sum(case when po.is_delivered = 1 then po.is_late else 0 end) as late_orders,
        avg(po.review_score) as average_review_score,
        sum(case when po.review_score is not null then 1 else 0 end) as reviewed_orders,
        sum(po.is_low_review) as low_review_orders
    from partner_orders po
    inner join sellers s
        on po.seller_id = s.seller_id
    group by
        po.seller_id,
        po.order_month,
        s.seller_city,
        s.seller_state
),

with_rates as (
    select
        *,
        cancelled_orders / nullif(order_count, 0)::double as cancellation_rate,
        late_orders / nullif(delivered_orders, 0)::double as late_delivery_rate,
        reviewed_orders / nullif(order_count, 0)::double as review_coverage_rate,
        low_review_orders / nullif(reviewed_orders, 0)::double as low_review_rate,
        lag(item_revenue) over (
            partition by seller_id
            order by order_month
        ) as previous_month_revenue
    from monthly
)

select
    seller_id || '-' || cast(order_month as varchar) as partner_month_key,
    *,
    (item_revenue - previous_month_revenue)
        / nullif(previous_month_revenue, 0)::double as revenue_growth_rate
from with_rates
