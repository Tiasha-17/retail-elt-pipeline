with order_items as (
    select * from {{ ref('fact_order_items') }}
),

reviews_by_order as (
    select
        order_id,
        avg(review_score) as review_score
    from {{ ref('fact_reviews') }}
    group by order_id
)

select
    oi.seller_id || '-' || oi.order_id as partner_order_key,
    oi.seller_id,
    oi.order_id,
    oi.customer_id,
    min(oi.order_date) as order_date,
    date_trunc('month', min(oi.order_date))::date as order_month,
    max(oi.order_status) as order_status,
    count(*) as item_count,
    sum(oi.price) as item_revenue,
    sum(oi.freight_value) as freight_value,
    sum(oi.price + oi.freight_value) as customer_value,
    max(oi.is_delivered) as is_delivered,
    max(oi.is_cancelled) as is_cancelled,
    max(oi.is_late) as is_late,
    max(oi.delivery_days) as delivery_days,
    max(r.review_score) as review_score,
    case when max(r.review_score) <= 2 then 1 else 0 end as is_low_review
from order_items oi
left join reviews_by_order r
    on oi.order_id = r.order_id
group by
    oi.seller_id,
    oi.order_id,
    oi.customer_id
