

with sales as (
    select * from "dataair"."staging"."stg_sales"
    where status = 'completed'
),

daily as (
    select
        order_date                        as sales_date,
        count(distinct order_id)          as order_count,
        sum(quantity)                     as units_sold,
        cast(sum(amount) as numeric(18, 2)) as total_amount
    from sales
    group by order_date
)

select
    sales_date,
    order_count,
    units_sold,
    total_amount
from daily


where sales_date >= (select coalesce(max(sales_date), date '1900-01-01') from "dataair"."marts"."sales_daily")
