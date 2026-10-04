
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
        select *
        from "dataair"."audit"."not_null_sales_daily_sales_date"
    
      
    ) dbt_internal_test