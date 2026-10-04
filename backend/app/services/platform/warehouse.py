"""Warehouse queries against the dataair database (raw/staging/marts/audit)."""
import logging
from typing import Any, Dict, List

from sqlalchemy import text

from backend.database import async_session_factory

logger = logging.getLogger(__name__)


async def _rows(sql: str, **params: Any) -> List[Dict[str, Any]]:
    async with async_session_factory() as db:
        result = await db.execute(text(sql), params)
        columns = list(result.keys())
        return [dict(zip(columns, row)) for row in result.fetchall()]


async def get_sales_daily(limit: int = 120) -> List[Dict[str, Any]]:
    return await _rows(
        """
        SELECT sales_date, order_count, units_sold, total_amount
        FROM marts.sales_daily
        ORDER BY sales_date DESC
        LIMIT :limit
        """,
        limit=limit,
    )


async def get_sales_summary() -> Dict[str, Any]:
    rows = await _rows(
        """
        SELECT
            count(*) AS days,
            sum(order_count) AS total_orders,
            sum(units_sold) AS total_units,
            sum(total_amount) AS total_revenue,
            avg(total_amount) AS avg_daily_revenue,
            max(total_amount) AS best_day_revenue,
            min(sales_date) AS first_day,
            max(sales_date) AS last_day
        FROM marts.sales_daily
        """
    )
    return rows[0] if rows else {}


async def get_top_products(limit: int = 10) -> List[Dict[str, Any]]:
    return await _rows(
        """
        SELECT p.product_id,
               upper(trim(p.product_name)) AS product_name,
               p.category,
               sum(s.quantity) AS units_sold,
               cast(sum(s.quantity * p.price) AS numeric(18, 2)) AS revenue
        FROM staging.stg_sales s
        JOIN staging.stg_products p ON p.product_id = s.product_id
        WHERE s.status = 'completed'
        GROUP BY p.product_id, p.product_name, p.category
        ORDER BY revenue DESC
        LIMIT :limit
        """,
        limit=limit,
    )


async def get_category_breakdown() -> List[Dict[str, Any]]:
    return await _rows(
        """
        SELECT p.category,
               count(DISTINCT s.order_id) AS orders,
               sum(s.quantity) AS units_sold,
               cast(sum(s.quantity * p.price) AS numeric(18, 2)) AS revenue
        FROM staging.stg_sales s
        JOIN staging.stg_products p ON p.product_id = s.product_id
        WHERE s.status = 'completed'
        GROUP BY p.category
        ORDER BY revenue DESC
        """
    )


async def get_elt_runs(limit: int = 50) -> List[Dict[str, Any]]:
    return await _rows(
        """
        SELECT run_id, model_name, layer, status,
               started_at, finished_at, duration_seconds, rows_affected
        FROM audit.elt_runs
        ORDER BY finished_at DESC NULLS LAST, created_at DESC
        LIMIT :limit
        """,
        limit=limit,
    )


async def get_quality_results(limit: int = 20) -> List[Dict[str, Any]]:
    return await _rows(
        """
        SELECT run_id, suite_name, checkpoint_name, status, success,
               result, created_at
        FROM audit.data_quality_results
        ORDER BY created_at DESC
        LIMIT :limit
        """,
        limit=limit,
    )


async def get_warehouse_overview() -> Dict[str, Any]:
    table_counts = await _rows(
        """
        SELECT table_schema, table_name
        FROM information_schema.tables
        WHERE table_schema IN ('raw', 'staging', 'marts', 'audit')
        ORDER BY table_schema, table_name
        """
    )
    return {
        "tables": [
            {"schema": row["table_schema"], "name": row["table_name"]}
            for row in table_counts
        ]
    }
