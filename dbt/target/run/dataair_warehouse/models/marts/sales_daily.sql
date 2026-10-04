
      
        
        
        delete from "dataair"."marts"."sales_daily" as DBT_INTERNAL_DEST
        where (sales_date) in (
            select distinct sales_date
            from "sales_daily__dbt_tmp020007737985" as DBT_INTERNAL_SOURCE
        );

    

    insert into "dataair"."marts"."sales_daily" ("sales_date", "order_count", "units_sold", "total_amount")
    (
        select "sales_date", "order_count", "units_sold", "total_amount"
        from "sales_daily__dbt_tmp020007737985"
    )
  