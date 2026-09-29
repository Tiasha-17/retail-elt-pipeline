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
    o.order_status,
    oi.price,
    oi.freight_value
from order_items oi
inner join orders o
    on oi.order_id = o.order_id
