with partner_orders as (
    select * from {{ ref('partner_order_performance') }}
),

sellers as (
    select * from {{ ref('dim_sellers') }}
),

scorecard_base as (
    select
        po.seller_id,
        s.seller_city,
        s.seller_state,
        min(po.order_date) as first_order_date,
        max(po.order_date) as latest_order_date,
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
        s.seller_city,
        s.seller_state
),

with_rates as (
    select
        *,
        cancelled_orders / nullif(order_count, 0)::double as cancellation_rate,
        late_orders / nullif(delivered_orders, 0)::double as late_delivery_rate,
        reviewed_orders / nullif(order_count, 0)::double as review_coverage_rate,
        low_review_orders / nullif(reviewed_orders, 0)::double as low_review_rate
    from scorecard_base
),

benchmarks as (
    select
        quantile_cont(item_revenue, 0.80) as revenue_p80,
        quantile_cont(order_count, 0.50) as orders_p50,
        quantile_cont(cancellation_rate, 0.75) as cancellation_rate_p75,
        quantile_cont(late_delivery_rate, 0.75) as late_delivery_rate_p75,
        quantile_cont(average_review_score, 0.25) as review_score_p25
    from with_rates
),

segmented as (
    select
        w.*,
        case
            when w.order_count >= 5
              and (
                w.cancellation_rate > b.cancellation_rate_p75
                or w.late_delivery_rate > b.late_delivery_rate_p75
                or w.average_review_score < b.review_score_p25
              )
                then 'At risk'
            when w.item_revenue >= b.revenue_p80
                then 'Strategic'
            when w.order_count >= b.orders_p50
              and coalesce(w.average_review_score, 0) >= 4.0
                then 'Growth opportunity'
            else 'Monitor'
        end as partner_segment
    from with_rates w
    cross join benchmarks b
)

select * from segmented
