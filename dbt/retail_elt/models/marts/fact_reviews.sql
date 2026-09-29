with reviews as (
    select * from {{ ref('stg_reviews') }}
),

orders as (
    select * from {{ ref('stg_orders') }}
)

select
    r.review_key,
    r.review_id,
    r.order_id,
    o.customer_id,
    o.order_purchase_date as order_date,
    r.review_score,
    r.review_comment_title,
    r.review_comment_message,
    r.review_creation_at,
    r.review_answered_at
from reviews r
inner join orders o
    on r.order_id = o.order_id
