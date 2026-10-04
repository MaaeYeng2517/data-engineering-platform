select
    product_id,
    product_name,
    category,
    price,
    _ingested_at
from (
    select
        *,
        row_number() over (
            partition by product_id
            order by _ingested_at desc nulls last
        ) as _row_number
    from (
        select
            cast(product_id as {{ dbt.type_string() }})   as product_id,
            upper(trim(product_name))                     as product_name,
            cast(category as {{ dbt.type_string() }})     as category,
            cast(price as numeric(18, 2))                 as price,
            _ingested_at
        from {{ source('raw', 'products') }}
        where product_id is not null
    ) casted
) deduplicated
where _row_number = 1
