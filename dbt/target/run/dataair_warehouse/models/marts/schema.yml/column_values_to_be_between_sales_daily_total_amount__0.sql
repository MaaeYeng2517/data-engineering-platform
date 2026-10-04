
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
        select *
        from "dataair"."audit"."column_values_to_be_between_sales_daily_total_amount__0"
    
      
    ) dbt_internal_test