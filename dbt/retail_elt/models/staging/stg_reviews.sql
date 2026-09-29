with source as (
    select * from {{ source('raw', 'reviews') }}
)

select
    -- review_id is NOT a reliable unique key in the raw Olist data: 789
    -- review_ids are reused across different order_ids. The composite
    -- (review_id, order_id) pair is unique, so that's the real natural key.
    review_id || '-' || order_id as review_key,
    review_id,
    order_id,
    cast(review_score as integer) as review_score,
    nullif(trim(review_comment_title), '') as review_comment_title,
    nullif(trim(review_comment_message), '') as review_comment_message,
    cast(review_creation_date as timestamp) as review_creation_at,
    cast(review_answer_timestamp as timestamp) as review_answered_at
from source
where review_id is not null
  and order_id is not null
