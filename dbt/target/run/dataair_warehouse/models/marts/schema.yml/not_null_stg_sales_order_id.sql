
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
        select *
        from "dataair"."audit"."not_null_stg_sales_order_id"
    
      
    ) dbt_internal_test