with source as (
    select * from {{ source('raw', 'products') }}
),

translation as (
    select * from {{ ref('stg_category_translation') }}
)

select
    p.product_id,
    coalesce(p.product_category_name, 'unknown') as product_category_name,
    coalesce(t.product_category_name_english, 'unknown') as product_category_name_english,
    cast(p.product_weight_g as integer) as product_weight_g,
    cast(p.product_length_cm as integer) as product_length_cm,
    cast(p.product_height_cm as integer) as product_height_cm,
    cast(p.product_width_cm as integer) as product_width_cm
from source p
left join translation t
    on p.product_category_name = t.product_category_name
where p.product_id is not null
