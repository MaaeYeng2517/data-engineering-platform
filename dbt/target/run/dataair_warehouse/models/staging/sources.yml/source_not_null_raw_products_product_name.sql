
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
        select *
        from "dataair"."audit"."source_not_null_raw_products_product_name"
    
      
    ) dbt_internal_test