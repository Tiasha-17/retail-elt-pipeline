with payments as (
    select * from {{ ref('stg_payments') }}
),

orders as (
    select * from {{ ref('stg_orders') }}
)

select
    p.order_id || '-' || cast(p.payment_sequential as varchar) as payment_key,
    p.order_id,
    o.customer_id,
    o.order_purchase_date as order_date,
    p.payment_sequential,
    p.payment_type,
    p.payment_installments,
    p.payment_value
from payments p
inner join orders o
    on p.order_id = o.order_id
