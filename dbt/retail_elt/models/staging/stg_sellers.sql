with source as (
    select * from {{ source('raw', 'sellers') }}
)

select
    seller_id,
    cast(seller_zip_code_prefix as varchar) as seller_zip_code_prefix,
    seller_city,
    upper(seller_state) as seller_state
from source
where seller_id is not null
