with order_items as (
    select * from {{ ref('stg_order_items') }}
),

orders as (
    select * from {{ ref('stg_orders') }}
)

select
    oi.order_id || '-' || cast(oi.order_item_id as varchar) as order_item_key,
    oi.order_id,
    oi.order_item_id,
    oi.product_id,
    oi.seller_id,
    o.customer_id,
    o.order_purchase_date as order_date,
    o.order_purchase_at,
    o.order_status,
    o.order_delivered_customer_at,
    o.order_estimated_delivery_at,
    case when o.order_status = 'delivered' then 1 else 0 end as is_delivered,
    case when o.order_status in ('canceled', 'unavailable') then 1 else 0 end as is_cancelled,
    case
        when o.order_status = 'delivered'
          and o.order_delivered_customer_at is not null
          and o.order_estimated_delivery_at is not null
        then case when o.order_delivered_customer_at > o.order_estimated_delivery_at then 1 else 0 end
        else null
    end as is_late,
    case
        when o.order_status = 'delivered'
          and o.order_delivered_customer_at is not null
        then datediff('day', o.order_purchase_at, o.order_delivered_customer_at)
        else null
    end as delivery_days,
    oi.price,
    oi.freight_value
from order_items oi
inner join orders o
    on oi.order_id = o.order_id
