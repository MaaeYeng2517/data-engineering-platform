with source as (
    select * from "dataair"."raw"."sales"
),

cleaned as (
    select
        cast(order_id as TEXT)      as order_id,
        cast(order_date as date)                       as order_date,
        cast(customer_id as TEXT)   as customer_id,
        cast(product_id as TEXT)    as product_id,
        cast(quantity as integer)                      as quantity,
        cast(amount as numeric(18, 2))                 as amount,
        cast(status as TEXT)        as status,
        _ingested_at
    from source
    where order_id is not null
      and amount is not null
),

deduplicated as (
    select
        *,
        row_number() over (
            partition by order_id, product_id, order_date
            order by _ingested_at desc nulls last
        ) as _row_number
    from cleaned
)

select
    order_id,
    order_date,
    customer_id,
    product_id,
    quantity,
    amount,
    status,
    _ingested_at
from deduplicated
where _row_number = 1