export interface SystemStatus {
  status: string
  [key: string]: unknown
}

export interface PlatformHealth {
  systems: Record<string, SystemStatus>
  summary: { total: number; healthy: number; unhealthy: number }
}

export interface PlatformLinks {
  airflow: string
  openmetadata: string
  prometheus: string
  grafana: string
}

export interface SalesDay {
  sales_date: string
  order_count: number
  units_sold: number
  total_amount: number
}

export interface SalesSummary {
  days?: number
  total_orders?: number
  total_units?: number
  total_revenue?: number
  avg_daily_revenue?: number
  best_day_revenue?: number
  first_day?: string
  last_day?: string
}

export interface TopProduct {
  product_id: string
  product_name: string
  category: string
  units_sold: number
  revenue: number
}

export interface CategoryBreakdown {
  category: string
  orders: number
  units_sold: number
  revenue: number
}

export interface EltRun {
  run_id: string
  model_name: string
  layer: string
  status: string
  started_at?: string
  finished_at?: string
  duration_seconds?: number
  rows_affected?: number
}

export interface QualityResult {
  run_id: string
  suite_name: string
  checkpoint_name: string
  status: string
  success: boolean
  result?: Record<string, unknown>
  created_at?: string
}

export interface WarehouseTable {
  schema: string
  name: string
}

export interface Dag {
  dag_id: string
  description?: string
  is_paused: boolean
  is_active: boolean
  schedule?: string
  tags: string[]
  file_path?: string
  next_run?: string
  url?: string
}

export interface DagRun {
  run_id: string
  state: string
  execution_date?: string
  start_date?: string
  end_date?: string
  conf?: Record<string, unknown>
}

export interface TaskInstance {
  task_id: string
  state?: string
  try_number?: number
  start_date?: string
  end_date?: string
  duration?: number
  operator?: string
}

export interface CatalogTable {
  id?: string
  name?: string
  type?: string
  fully_qualified_name?: string
  table_type?: string
  schema?: string
  database?: string
  description?: string
  updated_at?: number
  url?: string
}

export interface CatalogSearchResult {
  type?: string
  name?: string
  fully_qualified_name?: string
  description?: string
  href?: string
}

export interface LineageEdge {
  source?: string
  target?: string
}

export interface StorageBucket {
  name: string
  created_at?: string
}

export interface StorageObject {
  key: string
  size: number
  last_modified: string
  etag?: string
  storage_class?: string
  url?: string
}

export interface StorageStats {
  name: string
  object_count: number
  total_size: number
}

export interface MonitoringSample {
  metric: Record<string, string>
  value?: (string | number)[]
  values?: (string | number)[][]
}
