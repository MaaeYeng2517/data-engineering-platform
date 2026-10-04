
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
        select *
        from "dataair"."audit"."source_not_null_raw_customers_customer_id"
    
      
    ) dbt_internal_test