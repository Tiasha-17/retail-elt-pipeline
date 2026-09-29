with source as (
    select * from {{ source('raw', 'payments') }}
)

select
    order_id,
    cast(payment_sequential as integer) as payment_sequential,
    coalesce(payment_type, 'unknown') as payment_type,
    cast(payment_installments as integer) as payment_installments,
    cast(payment_value as decimal(10, 2)) as payment_value
from source
where order_id is not null
